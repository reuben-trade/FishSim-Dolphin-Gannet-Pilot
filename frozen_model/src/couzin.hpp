#ifndef COUZIN
#define COUZIN

#include "core.hpp"
#include "boundary.hpp"
#include "neighbour_list.hpp"


/*
 * Implementing the "couzin model"
 * see IDC JK RJ GDR NRF, J. theor. Biol., 2002 (10.1006/yjtbi.3065)
 */
class Couzin3D : public AVS3D {
    protected:
        VerletList<Coord3D> verlet_list_;
        double speed_,
               r_repel_,
               r_align_,
               r_attract_,
               a_percept_,
               v_turn_,
               dt_;
        Property align_gains_;
        Property attract_gains_;
        Property turn_multipliers_;
        Property external_gains_;
        Coord3D external_directions_;
        Coord3D saved_positions_;
        Coord3D saved_velocities_;
        Coord3D saved_orientations_;
        bool has_saved_state_ = false;
        Conn conn_repel_;
        Conn conn_align_;
        Conn conn_attract_;
        void rebuild_connections();
        bool is_visible(int i, int j); // agent i can see agent j
        Vec3D add_external_direction(int i, const Vec3D& social_direction);
        Vec3D controlled_direction(
            int i, const Vec3D& align_direction, const Vec3D& attract_direction
        );
        inline void update_velocity(){
            velocities_ = orientations_ * speed_;
        };

    public:
        Coord3D positions_;
        Coord3D velocities_;  // velocities_ represent the target moving direction
        Couzin3D(
            int n,
            double rr, double ro, double ra,  // repel, align, attract ranges
            double ap,  // angle of perception
            double eta, // noise
            double v0,  // speed
            double vt,  // turning rate
            double dt   // delta time
        );
        void move(bool rebuild);
        void evolve(int steps, bool rebuild);
        void set_agent_control(
            int index,
            double align_gain,
            double attract_gain,
            double turn_multiplier,
            std::vector<double> external_direction,
            double external_gain
        );
        void reset_agent_control(int index);
        void reset_controls();
        void set_noise(double noise);
        void save_state();
        void restore_state();
        // Remove current indices; return old survivor indices in preserved order.
        Indices remove_agents(const Indices& indices);
        inline Coord3D& get_positions() { return positions_; };
        void load_positions(Coord3D);
        inline Coord3D& get_velocities() { return velocities_; };
        void load_velocities(Coord3D);
        inline double get_polarisation(){
            if (n_ == 0) { return 0.0; }
            return velocities_.rowwise().sum().norm() / n_;
        }
        inline double get_mill(){
            if (n_ < 2) { return 0.0; }
            return get_mill_order(velocities_, positions_);
        }
};


class CouzinTank3D : public Couzin3D {
    BoundaryTank3D tank_;
    Gravity gravity_;

    public:
        CouzinTank3D(
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
            double g   // strength of gravith
        );
        void move_in_tank(bool rebuild);
        inline void evolve_in_tank(int steps, bool rebuild){
            for (int i = 0; i < steps; i++){
                this->move_in_tank(rebuild);
            }
        };
};


#endif
