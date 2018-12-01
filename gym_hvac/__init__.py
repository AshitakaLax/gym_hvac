from gym.envs.registration import register

register(
    id='Hvac-v0',
    entry_point='gym_hvac.envs:HvacEnv',
)