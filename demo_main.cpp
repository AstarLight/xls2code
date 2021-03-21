#include <iostream>
#include <map>
#include <stdio.h>
#include "auto_codes/game_time_conf.h"

using namespace std;

int main()
{

	std::map<int, std::map<string, string> > my_conf = get_conf();
	printf("%s\n", my_conf[2101]["season_name"].c_str());
	printf("%s\n", my_conf[2102]["release_start"].c_str());
    return 0;
}
