import sys, importlib, time
sys.path.insert(0, '.')
import kaggle_environments as ke

SEEDS = [101, 202, 303, 404, 505]

def run_solo(agent_fn, opp='pass', seeds=SEEDS):
    vals = []
    for s in seeds:
        env = ke.make('kaggriculture', configuration={'episodeSteps':720, 'seed': s}, debug=False)
        env.run([agent_fn, opp])
        vals.append(env.steps[-1][0].reward)
    return vals

if __name__ == '__main__':
    import agent_dev
    importlib.reload(agent_dev)
    vals = run_solo(agent_dev.agent)
    print('vals', vals, 'mean', sum(vals)/len(vals))
