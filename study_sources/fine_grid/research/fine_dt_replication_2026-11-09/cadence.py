"""Physical-time diagnostic clocks; no model decisions or stepping."""
DT=.000625
SAMPLE_INTERVAL=.1
PROGRESS_INTERVAL=1.
def exact_steps(interval,dt=DT):
 n=round(interval/dt)
 if n<=0 or abs(n*dt-interval)>1e-12:raise ValueError('Diagnostic interval must contain exact positive steps')
 return n
SAMPLE_STEPS=exact_steps(SAMPLE_INTERVAL)
PROGRESS_STEPS=exact_steps(PROGRESS_INTERVAL)
def due(number,steps,stride):
 if isinstance(number,bool) or int(number)!=number or not 0<=number<=steps:raise ValueError('Invalid diagnostic step')
 return number%stride==0 or number==steps
def sample_due(number,steps):return due(number,steps,SAMPLE_STEPS)
def progress_due(number,steps):return due(number,steps,PROGRESS_STEPS)
