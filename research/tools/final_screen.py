import sys, json
sys.path.insert(0, '.')
import tournament as T
import frozen_1062

seeds = [9001,9002,9003,9004,9005,9006,9007,9008,9009,9010]
opps = {'pass':'pass','random':'random','starter':'starter','frozen_1062':frozen_1062.agent}
rows = T.run_matrix(seeds, opps, tag='final')
with open('final_screen.json','w') as f:
    json.dump(rows, f)
T.summarize(rows, 'FINAL SCREEN (challenger)')

# Also record frozen_1062 vs weak baselines, for the required direct comparison.
rows2 = T.run_matrix(seeds, {'pass':'pass','random':'random','starter':'starter'}, challenger=frozen_1062.agent, tag='frozen_vs_weak')
with open('frozen_vs_weak.json','w') as f:
    json.dump(rows2, f)
T.summarize(rows2, 'FROZEN_1062 vs weak baselines (context)')
print("ALL DONE")
