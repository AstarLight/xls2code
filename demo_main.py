import auto_codes.game_time_conf as time_conf
import auto_codes.game_reward_conf as reward_conf
import auto_codes.game_guide_conf as guide_conf

conf_time = time_conf.get_conf()
print(conf_time)

conf_reward = reward_conf.get_conf()
print(conf_reward[21011028])


conf_guide = guide_conf.get_conf()
print(conf_guide[3]["desc"], conf_guide[3]["npc"])

