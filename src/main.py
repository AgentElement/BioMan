from config import Config
from environment import Environment


def main():
    env = Environment(Config())
    env.simulate()


if __name__ == '__main__':
    main()
