#include "simulator.hpp"
#include <iostream>

Action drs_train_follower(const State& s, double gap) {
    if (gap > 0.0 && gap < 1.5 && s.tire_age < 28) return {false, "Soft"}; 
    return (s.tire_age > 18) ? Action{true, "Medium"} : Action{false, "Soft"};
}

Action aggressive_undercut(const State& s, double gap) {
    if (gap > 0.5 && gap < 1.8 && s.tire_age > 10) return {true, "Soft"};
    return (s.tire_age > 22) ? Action{true, "Medium"} : Action{false, "Soft"};
}

Action defensive_leader(const State& s, double gap) {
    if (gap < 0 && gap > -1.2 && s.tire_age > 15) return {true, "Medium"}; 
    return (s.tire_age > 25) ? Action{true, "Hard"} : Action{false, "Soft"};
}



int main() {
    RaceSimulator sim;
    sim.add_car("Defensive Lead", defensive_leader, 110.0);
    sim.add_car("Follower 1", drs_train_follower, 110.0);
    sim.add_car("Follower 2", drs_train_follower, 110.0);
    sim.add_car("Attacker", aggressive_undercut, 110.0);

    sim.simulate_race(50); 
    sim.print_results();   
    return 0;
}


