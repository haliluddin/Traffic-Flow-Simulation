Traffic Flow Simulation Documentation

Overview

This simulation models a four-way intersection with traffic lights. Vehicles of different types (cars, buses, trucks, bikes) are generated randomly, approach the intersection from four directions, and navigate according to traffic signal timings and lane choices. The simulation incorporates lane changes, vehicle turning behavior, and realistic vehicle movement based on speeds. The simulation runs for a predefined time.

Key Components

Traffic Signals - The simulation manages four traffic signals, each with red, yellow, and green phases.  
Vehicles - Vehicles are represented as sprites with different types (car, bus, truck, bike), each having a defined speed. Vehicles are generated randomly and assigned to lanes and directions. They follow traffic rules, stopping at red lights and proceeding when the light is green. Vehicles can choose to turn or go straight.
Vehicle Movement - Vehicle movement is simulated based on their speed and the presence of other vehicles. A stopping gap and a moving gap are maintained to prevent collisions.
Lane Management - The simulation handles three lanes per direction. Vehicles in the inner lanes can turn, while vehicles in the outer lane must go straight.
GUI - A graphical user interface (GUI) using Pygame displays the intersection, vehicles, and traffic signals. Signal timers are shown visually.
Simulation Time - The simulation runs for a predetermined time, after which it terminates.

Instructions on How to Run

1. Clone this repository.
2. Open the folder in your preferred Python IDE (e.g., PyCharm, VS Code).
3. Install the Pygame library using the command pip install pygame.
4. Execute the main.py file You can run it from your terminal using python simulation.py.
5. The simulation will start automatically.
