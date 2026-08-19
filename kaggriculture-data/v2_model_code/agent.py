from state import GameState
from planner import Planner


def agent(obs):

    state = GameState.from_obs(obs)

    planner = Planner(state)

    return planner.play().to_dict()
