# this is a simple implementation of the hvac_gym
import gym
import gym_hvac

env = gym.make('Hvac-v0')

for	i in range(3600):
    if not hvac.HeatingIsShuttingDown and hvac.HeatingIsOn and hvacBuilding.current_temperature > 18.8889:#21:
        print("Turning the Heater Off")
        hvac.TurnHeatingOff()

    if hvac.HeatingIsOn == False and hvacBuilding.current_temperature < 17.7778:#17:
        print("Turning the Heater On")
        numberOfHeatingOn = numberOfHeatingOn + 1
        hvac.TurnHeatingOn()