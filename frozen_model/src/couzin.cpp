#include "couzin.hpp"


Coord3D random_pos_no_overlap(double d, int n){
    std::vector<Vec3D> positions;
    Coord3D coordinates_no_overlap {3, n};
    double D = d * pow((double) 10.0 / 1.0 * n, 1.0 / 3.0);
    double pz, pxy, theta, r;
    Vec3D p;
    for (int i = 0; i < n; i++){
        bool overlap = true;
        while (overlap){
            overlap = false;
            pz = (double) 2 * rand() / (RAND_MAX) - 1;  // U(-1, 1)
            theta = (double) rand() / (RAND_MAX) * M_PI * 2;  // U(0, 2*pi)
            r = (double) rand() / (RAND_MAX) * D / 2;  // U(0, D)
            pxy = sqrt(1 - pow(pz, 2));
            p << pxy * cos(theta) * r, pxy * sin(theta) * r , pz * r;
            for (auto p2 : positions){
                double dist = (p2 - p).norm();
                if (dist < d){
                    overlap = true;
                }
            }
        }
        positions.push_back(p);
    }

    for (int i = 0; i < n; i++){
        coordinates_no_overlap.col(i) = positions[i];
    }

    return coordinates_no_overlap;
}


Couzin3D::Couzin3D(
    int n, double rr, double ro, double ra, double ap,
    double eta, double v0, double vt, double dt
) :
    AVS3D{n, eta}, verlet_list_{ra, ra * 3}, speed_(v0),
    r_repel_(rr), r_align_(ro), r_attract_(ra),
    a_percept_(ap), v_turn_(vt), dt_(dt),
    align_gains_{n}, attract_gains_{n}, turn_multipliers_{n},
    external_gains_{n}, external_directions_{3, n},
    positions_{3, n}, velocities_{3, n}
{
    reset_controls();
    velocities_ = orientations_;
    positions_ = random_pos_no_overlap(rr, n);
}


void Couzin3D::load_positions(Coord3D positions){
    if (positions.cols() != n_ || !positions.allFinite()){
        throw std::invalid_argument(
            "positions must have shape (3, n) and contain finite values"
        );
    }
    this->positions_ = positions;
    rebuild_connections();
}


void Couzin3D::load_velocities(Coord3D velocities){
    if (velocities.cols() != n_ || !velocities.allFinite()){
        throw std::invalid_argument(
            "velocities must have shape (3, n) and contain finite values"
        );
    }
    for (int i = 0; i < n_; i++){
        const double norm = velocities.col(i).norm();
        if (norm <= _EPS){
            throw std::invalid_argument("velocity directions must be non-zero");
        }
        velocities.col(i) /= norm;
    }
    velocities_ = velocities;
    orientations_ = velocities;
}


void Couzin3D::rebuild_connections(){
    verlet_list_.build(positions_);
    std::vector<Conn> conn_list = verlet_list_.get_neighbour_conn_slow(
        positions_, std::vector<double>{0, r_repel_, r_align_, r_attract_}
    );
    conn_repel_ = conn_list[0];
    conn_align_ = conn_list[1];
    conn_attract_ = conn_list[2];
}


bool Couzin3D::is_visible(int i, int j){
    Vec3D v1, v2;
    v1 = velocities_.col(i);
    v2 = positions_.col(j) - positions_.col(i);
    const double denominator = v1.norm() * v2.norm();
    if (denominator <= _EPS){
        return false;
    }
    const double cosine = std::max(
        -1.0, std::min(1.0, v1.dot(v2) / denominator)
    );
    double aij = abs(acos(cosine));
    if (aij < a_percept_){
        return true;
    }
    return false;
}


Vec3D Couzin3D::add_external_direction(
    int i, const Vec3D& social_direction
){
    Vec3D desired = social_direction;
    if (external_gains_(i) > 0){
        desired += external_gains_(i) * external_directions_.col(i);
    }
    if (!desired.allFinite() || desired.norm() <= _EPS){
        desired = velocities_.col(i);
    }
    if (!desired.allFinite() || desired.norm() <= _EPS){
        desired = Vec3D::UnitX();
    }
    return desired / desired.norm();
}


Vec3D Couzin3D::controlled_direction(
    int i, const Vec3D& align_direction, const Vec3D& attract_direction
){
    Vec3D social_direction = (
        align_gains_(i) * align_direction
        + attract_gains_(i) * attract_direction
    );
    return add_external_direction(i, social_direction);
}


void Couzin3D::set_agent_control(
    int index,
    double align_gain,
    double attract_gain,
    double turn_multiplier,
    std::vector<double> external_direction,
    double external_gain
){
    if (index < 0 || index >= n_){
        throw std::out_of_range("agent control index is out of range");
    }
    if (
        !std::isfinite(align_gain) || align_gain < 0
        || !std::isfinite(attract_gain) || attract_gain < 0
        || !std::isfinite(turn_multiplier) || turn_multiplier < 0
        || !std::isfinite(external_gain) || external_gain < 0
    ){
        throw std::invalid_argument("agent control gains must be finite and non-negative");
    }
    if (external_direction.size() != 3){
        throw std::invalid_argument("external direction must have three components");
    }
    if (
        !std::isfinite(external_direction[0])
        || !std::isfinite(external_direction[1])
        || !std::isfinite(external_direction[2])
    ){
        throw std::invalid_argument("external direction must be finite");
    }

    Vec3D direction {
        external_direction[0], external_direction[1], external_direction[2]
    };

    align_gains_(index) = align_gain;
    attract_gains_(index) = attract_gain;
    turn_multipliers_(index) = turn_multiplier;
    external_gains_(index) = external_gain;
    if (direction.norm() > _EPS){
        external_directions_.col(index) = direction.normalized();
    } else {
        external_directions_.col(index).setZero();
        external_gains_(index) = 0;
    }
}


void Couzin3D::reset_agent_control(int index){
    if (index < 0 || index >= n_){
        throw std::out_of_range("agent control index is out of range");
    }
    align_gains_(index) = 1;
    attract_gains_(index) = 1;
    turn_multipliers_(index) = 1;
    external_gains_(index) = 0;
    external_directions_.col(index).setZero();
}


void Couzin3D::reset_controls(){
    align_gains_.setOnes();
    attract_gains_.setOnes();
    turn_multipliers_.setOnes();
    external_gains_.setZero();
    external_directions_.setZero();
}


void Couzin3D::set_noise(double noise){
    if (!std::isfinite(noise) || noise < 0 || noise > 1){
        throw std::invalid_argument("noise must be finite and in the range [0, 1]");
    }
    noise_ = noise;
}


void Couzin3D::save_state(){
    saved_positions_ = positions_;
    saved_velocities_ = velocities_;
    saved_orientations_ = orientations_;
    has_saved_state_ = true;
}


void Couzin3D::restore_state(){
    if (!has_saved_state_){
        throw std::runtime_error("no Couzin state has been saved");
    }
    positions_ = saved_positions_;
    velocities_ = saved_velocities_;
    orientations_ = saved_orientations_;
    n_ = positions_.cols();
    align_gains_.resize(1, n_);
    attract_gains_.resize(1, n_);
    turn_multipliers_.resize(1, n_);
    external_gains_.resize(1, n_);
    external_directions_.resize(3, n_);
    reset_controls();
    rebuild_connections();
}


Indices Couzin3D::remove_agents(const Indices& indices){
    std::vector<bool> removed(n_, false);
    for (int index : indices){
        if (index < 0 || index >= n_){
            throw std::out_of_range("removal index is out of range");
        }
        if (removed[index]){
            throw std::invalid_argument("removal indices must be unique");
        }
        removed[index] = true;
    }

    Indices survivors;
    survivors.reserve(n_ - indices.size());
    for (int old_index = 0; old_index < n_; old_index++){
        if (removed[old_index]) { continue; }
        const int new_index = survivors.size();
        survivors.push_back(old_index);
        if (new_index == old_index) { continue; }
        positions_.col(new_index) = positions_.col(old_index);
        velocities_.col(new_index) = velocities_.col(old_index);
        orientations_.col(new_index) = orientations_.col(old_index);
        align_gains_(new_index) = align_gains_(old_index);
        attract_gains_(new_index) = attract_gains_(old_index);
        turn_multipliers_(new_index) = turn_multipliers_(old_index);
        external_gains_(new_index) = external_gains_(old_index);
        external_directions_.col(new_index) = external_directions_.col(old_index);
    }
    n_ = survivors.size();
    positions_.conservativeResize(Eigen::NoChange, n_);
    velocities_.conservativeResize(Eigen::NoChange, n_);
    orientations_.conservativeResize(Eigen::NoChange, n_);
    align_gains_.conservativeResize(1, n_);
    attract_gains_.conservativeResize(1, n_);
    turn_multipliers_.conservativeResize(1, n_);
    external_gains_.conservativeResize(1, n_);
    external_directions_.conservativeResize(Eigen::NoChange, n_);
    rebuild_connections();
    return survivors;
}


void Couzin3D::move(bool rebuild){
    if (n_ == 0) { return; }
    if (rebuild) {
        rebuild_connections();
    }

    Vec3D shift_ij, oi, vj, oi_attr_, oi_align_;
    double dij = 0;

    for (int i = 0; i < n_; i++){  // determine the target orientations
        if (conn_repel_[i].size() > 0){  // repel dominate
            oi << 0, 0, 0;
            for (auto j : conn_repel_[i]){
                shift_ij = positions_.col(j) - positions_.col(i);
                dij = shift_ij.norm();
                if (dij > _EPS){
                    oi -= shift_ij / dij;
                }
            }
            if (!oi.allFinite() || oi.norm() <= _EPS){
                oi = velocities_.col(i);
            } else {
                oi.normalize();
            }
            orientations_.col(i) = add_external_direction(i, oi);
            continue;
        }

        oi_align_ << velocities_.col(i);
        for (auto j : conn_align_[i]){
            if (is_visible(i, j)) {
                vj = velocities_.col(j);
                oi_align_ += vj;
            }
        }
        if (oi_align_.allFinite() && oi_align_.norm() > _EPS){
            oi_align_ = oi_align_ / oi_align_.norm();
        } else {
            oi_align_ = velocities_.col(i);
        }

        bool see_neighbour = false;
        oi_attr_ << 0, 0, 0;
        for (auto j : conn_attract_[i]){
            if (is_visible(i, j)) {
                shift_ij = positions_.col(j) - positions_.col(i);
                dij = shift_ij.norm();
                if (dij > _EPS){
                    oi_attr_ += shift_ij / dij;
                    see_neighbour = true;
                }
            }
        }
        if (see_neighbour && oi_attr_.norm() > _EPS){
            oi_attr_ = oi_attr_ / oi_attr_.norm();
        } else {
            oi_attr_.setZero();
        }

        orientations_.col(i) = controlled_direction(i, oi_align_, oi_attr_);
    }

    this->add_noise();  // rotate orientations_ randomly

    // try to align velocities to gargeted directions
    for (int i = 0; i < n_; i++){
        Vec3D vi_old = velocities_.col(i);
        Vec3D vi_target = orientations_.col(i);
        RotMat R = get_rotation_matrix(
            vi_old, vi_target, v_turn_ * turn_multipliers_(i) * dt_
        );
        velocities_.col(i) << R * vi_old;
    }
    positions_ += velocities_ * speed_ * dt_;
}


void Couzin3D::evolve(int steps, bool rebuild){
    for (int i = 0; i < steps; i++){
        this->move(rebuild);
    }
}


CouzinTank3D::CouzinTank3D(
            int n,
            double rr, double ro, double ra,  // repel, align, attract ranges
            double ap,  // angle of perception
            double eta, // noise
            double v0,  // speed
            double vt,  // turning rate
            double dt,  // delta time
            double c,   // shape parameter for tank
            double h,   // height of tank
            double kw,   // strength of wall interaction
            bool align_cap,   // true: align with wall; false: reflect from wall
            bool align_base,   // true: align with wall; false: reflect from wall
            double g   // gravity strength
        ) :
    Couzin3D(n, rr, ro, ra, ap, eta, v0, vt, dt),
    tank_{c, h, kw, align_cap, align_base}, gravity_{g}
{
    positions_ = tank_.get_random_positions(n);
    tank_.fix_orientations(positions_, orientations_, dt_);
}


void CouzinTank3D::move_in_tank(bool rebuild){
    if (n_ == 0) { return; }
    if (rebuild) {
        rebuild_connections();
    }

    Vec3D shift_ij, oi, vj, oi_attr_, oi_align_;
    double dij = 0;

    for (int i = 0; i < n_; i++){  // determine the target orientations
        if (conn_repel_[i].size() > 0){  // repel dominate
            oi << 0, 0, 0;
            for (auto j : conn_repel_[i]){
                shift_ij = positions_.col(j) - positions_.col(i);
                dij = shift_ij.norm();
                if (dij > _EPS){
                    oi -= shift_ij / dij;
                }
            }
            if (!oi.allFinite() || oi.norm() <= _EPS){
                oi = velocities_.col(i);
            } else {
                oi.normalize();
            }
            orientations_.col(i) = add_external_direction(i, oi);
            continue;
        }

        oi_align_ << velocities_.col(i);
        for (auto j : conn_align_[i]){
            if (is_visible(i, j)) {
                vj = velocities_.col(j);
                oi_align_ += vj;
            }
        }
        if (oi_align_.allFinite() && oi_align_.norm() > _EPS){
            oi_align_ = oi_align_ / oi_align_.norm();
        } else {
            oi_align_ = velocities_.col(i);
        }

        bool see_neighbour = false;
        oi_attr_ << 0, 0, 0;
        for (auto j : conn_attract_[i]){
            if (is_visible(i, j)) {
                shift_ij = positions_.col(j) - positions_.col(i);
                dij = shift_ij.norm();
                if (dij > _EPS){
                    oi_attr_ += shift_ij / dij;
                    see_neighbour = true;
                }
            }
        }
        if (see_neighbour && oi_attr_.norm() > _EPS){
            oi_attr_ = oi_attr_ / oi_attr_.norm();
        } else {
            oi_attr_.setZero();
        }

        orientations_.col(i) = controlled_direction(i, oi_align_, oi_attr_);
    }

    this->add_noise();  // rotate orientations_ randomly


    // try to align velocities to gargeted directions
    for (int i = 0; i < n_; i++){
        Vec3D vi_old = velocities_.col(i);
        Vec3D vi_target = orientations_.col(i);
        RotMat R = get_rotation_matrix(
            vi_old, vi_target, v_turn_ * turn_multipliers_(i) * dt_
        );
        velocities_.col(i) << R * vi_old;
    }

    gravity_.fix_orientations(positions_, velocities_, dt_);
    tank_.fix_orientations(positions_, velocities_, dt_);

    positions_ += velocities_ * speed_ * dt_;
    tank_.fix_positions(positions_, dt_);
}
