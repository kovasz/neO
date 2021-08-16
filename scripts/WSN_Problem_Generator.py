import argparse
import os
import shutil
from datetime import datetime
import json
import random as rnd
import networkx as nx
import pylab as pl
import math as mt


class GraphCheck:
    @staticmethod
    def enough_crits_in_range(sensor_positions, number_critical_points, critical_points, sensor_ranges):
        inrange_crit = 0
        for j in range(0, number_critical_points):
            for i in range(0, number_of_sensors):
                if int(mt.sqrt(
                        mt.pow((sensor_positions[i + 1][0] - critical_points[j]["x"]), 2) +
                        mt.pow((sensor_positions[i + 1][1] - critical_points[j]["y"]), 2))) < sensor_ranges[i][1]:
                    inrange_crit += 1
                    break

        if inrange_crit >= int(number_critical_points * 0.4):
            return True
        else:
            return False

    @staticmethod
    def plain_bfs_digraph(g, source):
        seen = set()
        next_level = {source}
        while next_level:
            this_level = next_level
            next_level = set()
            for v in this_level:
                if v not in seen:
                    yield v
                    seen.add(v)
                    for i in g[v]:
                        if g.has_edge(v, i):
                            next_level.add(i)

    @staticmethod
    def is_connected_digraph(g):
        if len(g) == 0:
            raise nx.NetworkXPointlessConcept("Connectivity is undefined for the null graph.")
        is_conn = 1
        for i in g:
            if g.out_degree(i) == 0 or g.in_degree(i) == 0:
                is_conn = 0
                break
        sum = 0
        if is_conn == 1:
            for i in g:
                if len(set(GraphCheck.plain_bfs_digraph(g, i))) == len(g):
                    sum = sum + 1
                else:
                    return False
            if sum == len(g):
                return True
        else:
            return False


class Model(object):
    def __init__(self, index, model_name, sensor_coordinates=None, target_coordinates=None):
        self.sensor_graph = nx.DiGraph()
        self.sensor_and_target_graph = nx.DiGraph()
        self.sensor_ranges = [[]]
        self.critical_points = []
        self.targets = []
        self.sensors = []
        self.sensor_coordinates = sensor_coordinates
        self.target_coordinates = target_coordinates
        self.fig = None
        self.index = index
        self.model_name = model_name

    def set_sensor_coordinate(self, i):
        x = self.sensor_coordinates[i - 1]["x"]
        y = self.sensor_coordinates[i - 1]["y"]

        self.sensor_graph.add_node(i, pos=(x, y))
        self.sensor_and_target_graph.add_node(i, pos2=(x, y))
        return x, y

    def generate_sensors(self):
        raise NotImplementedError()

    def generate_targets(self):
        self.targets = []
        for i in range(1, number_of_targets + 1):
            x = self.target_coordinates[i - 1]["x"]
            y = self.target_coordinates[i - 1]["y"]
            target = {
                "x": x,
                "y": y,
                "critical": True if i < (number_of_targets + 1) / 2 else False
            }
            self.targets.append(target)

            self.sensor_and_target_graph.add_node(number_of_sensors + i, pos2=(x, y))

            self.sensor_and_target_graph.nodes.values()

            if plot:
                if i <= number_of_targets / 2:
                    # self.fig.gca().add_artist(pl.Circle((x, y), 4, color="yellow", fill=True))
                    self.sensor_and_target_graph.nodes[number_of_sensors + i]['category'] = 2
                else:
                    # self.fig.gca().add_artist(pl.Circle((x, y), 4, color="green", fill=True))
                    self.sensor_and_target_graph.nodes[number_of_sensors + i]['category'] = 1

        for i in range(0, int(number_of_targets / 2)):
            self.critical_points.append(self.targets[i])

    def generate_file_content(self):
        raise NotImplementedError()

    def specified_data_writing(self):
        with open(out_dir + self.model_name + "/data/" + str(self.index) + "_Graph.out", "a") as myfile:
            myfile.write("Number of sensors: " + str(number_of_sensors) + '\n')
            myfile.write("Number of targets: " + str(number_of_targets) + '\n')
            myfile.write("Territory range: x = " + str(x_max) + " y = " + str(y_max) + '\n')
            myfile.write("Number of edges: " + str(self.sensor_and_target_graph.number_of_edges()) + '\n')
            myfile.write("Number of vertices: " + str(number_of_sensors) + '\n')
            myfile.write("Theoretical minimum : " + str(
                float(number_of_sensors) / float((number_of_sensors * (number_of_sensors - 1)))) + '\n')
            myfile.write("Density of the graph: " + str(nx.density(self.sensor_and_target_graph)) + '\n')

    def generating_communication_graph(self, sensor_and_target_positions):
        for i in range(1, number_of_sensors + 1):
            for j in range(1, number_of_sensors + 1 + number_of_targets):
                x1, y1 = sensor_and_target_positions[i]
                x2, y2 = sensor_and_target_positions[j]
                if i != j and (mt.sqrt(mt.pow((x2 - x1), 2) + mt.pow((y2 - y1), 2))) <= self.sensor_ranges[i - 1][1]:
                    self.sensor_and_target_graph.add_edge(i, j)
                    if j > number_of_sensors:
                        self.sensor_and_target_graph.add_edge(j, i)

    def communication_graph_optimized_plot(self, path):
        pl.figure()
        pl.plot()
        pl.title("Communication graph")
        nx.draw(self.sensor_and_target_graph, with_labels=True)
        pl.savefig(path + "/Comm_graph.png")
        # pl.close()
        return

    def generating_network(self):
        sensor_positions = []
        sensor_and_target_positions = []
        tries = 0

        while True:
            if not shared:
                self.sensor_coordinates = generate_coordinates(number_of_sensors, range_x, range_y, min_distance_sensor)
                self.target_coordinates = generate_coordinates(number_of_targets, range_x, range_y, min_distance_target)
            self.sensor_graph.clear()
            self.sensor_and_target_graph.clear()
            sensor_positions.clear()
            sensor_and_target_positions.clear()
            self.sensor_ranges.clear()
            self.critical_points.clear()

            if plot:
                pl.rcParams['figure.figsize'] = 10, 10
                self.fig = pl.gcf()
                ax = pl.gca()
                ax.cla()
                ax.set_xlim((0, x_max))
                ax.set_ylim((0, y_max))

            self.generate_sensors()
            sensor_positions = (nx.get_node_attributes(self.sensor_graph, 'pos'))

            self.generate_targets()
            sensor_and_target_positions = (nx.get_node_attributes(self.sensor_and_target_graph, 'pos2'))

            self.generating_communication_graph(sensor_and_target_positions)

            # print("Connected:" + str(GraphCheck.is_connected_digraph(self.sensor_and_target_graph)))
            # print("Density:" + str(nx.density(self.sensor_and_target_graph)))
            if GraphCheck.is_connected_digraph(self.sensor_and_target_graph) and GraphCheck.enough_crits_in_range(
                    sensor_positions, int(number_of_targets / 2), self.critical_points,
                    self.sensor_ranges) and upper_bound >= nx.density(self.sensor_and_target_graph) >= lower_bound:
                content = self.generate_file_content()

                json_object = json.dumps(content, indent=4)
                with open(out_dir + self.model_name + "/networks/" + str(self.index) + ".wsn", "w") as out_file:
                    out_file.write(json_object)
                    out_file.close()
                self.specified_data_writing()

                if plot:
                    path = out_dir + self.model_name + "/image/{}".format(self.index)
                    os.makedirs(path)
                    color_map = {0: 'r', 1: 'b', 2: 'y'}
                    nx.draw(self.sensor_and_target_graph, sensor_and_target_positions, with_labels=False,
                            node_color=[color_map[self.sensor_and_target_graph.nodes[node]['category']] for node in
                                        self.sensor_and_target_graph])
                    nx.draw_networkx_labels(self.sensor_and_target_graph, sensor_and_target_positions, labels,
                                            font_size=14)
                    pl.title("Randomly Deployed Placement")
                    pl.savefig(path + "/Sensors_placement.png")
                    pl.close()
                    self.communication_graph_optimized_plot(path)
                return True
            elif tries > 5:
                return False
            tries += 1


class Model1(Model):
    def __init__(self, index, model_name, sensor_coordinates=None, target_coordinates=None, is_fix_scope=False):
        super().__init__(index, model_name, sensor_coordinates, target_coordinates)
        self.fix_scope = is_fix_scope

    def generate_file_content(self):
        return {
            "version": 1,
            "sensors": self.sensors,
            "points": self.targets
        }

    def generate_sensors(self):
        self.sensors = []
        for i in range(1, number_of_sensors + 1):
            x, y = self.set_sensor_coordinate(i)

            if self.fix_scope:
                scope = fix_scope
            else:
                scope = DISCRETE_SCOPES[rnd.randrange(len(DISCRETE_SCOPES))]

            sensor = {
                "x": x,
                "y": y,
                "range": scope
            }

            self.sensors.append(sensor)
            self.sensor_ranges.append([i, scope])

            if plot:
                circle = pl.Circle((x, y), scope, color="blue", fill=False)
                self.fig.gca().add_artist(circle)

            self.sensor_graph.nodes.values()
            self.sensor_graph.nodes[i]['category'] = 0

            self.sensor_and_target_graph.nodes.values()
            self.sensor_and_target_graph.nodes[i]['category'] = 0


class Model2(Model):
    def __init__(self, index, model_name, sensor_coordinates=None, target_coordinates=None, is_fix_power=False):
        super().__init__(index, model_name, sensor_coordinates, target_coordinates)
        self.fix_power = is_fix_power

    def generate_file_content(self):
        return {
            "version": 2,
            "sensors": self.sensors,
            "points": self.targets,
            "levels": POWER_LEVELS
        }

    def generate_sensors(self):
        self.sensors = []
        for i in range(1, number_of_sensors + 1):
            x, y = self.set_sensor_coordinate(i)

            if self.fix_power:
                power = fix_power
            else:
                power = rnd.randrange(200, max_power)

            sensor = {
                "x": x,
                "y": y,
                "power": power
            }

            self.sensors.append(sensor)
            self.sensor_ranges.append([i, 64])

            if plot:
                circle = pl.Circle((x, y), 64, color="blue", fill=False)
                self.fig.gca().add_artist(circle)

            self.sensor_graph.nodes.values()
            self.sensor_graph.nodes[i]['category'] = 0

            self.sensor_and_target_graph.nodes.values()
            self.sensor_and_target_graph.nodes[i]['category'] = 0


def remove_files_by_index(index):
    models = ["model_1", "model_1_fix", "model_2", "model_2_fix"]
    for i in range(0, len(models)):
        if os.path.isfile(out_dir + models[i] + "/networks/" + str(index) + ".wsn"):
            os.remove(out_dir + models[i] + "/networks/" + str(index) + ".wsn")
            os.remove(out_dir + models[i] + "/data/" + str(index) + "_Graph.out")
            shutil.rmtree(out_dir + models[i] + "/image/" + str(index))


def has_distance_with_all(points, x, y, dist):
    for point in points:
        if mt.sqrt(mt.pow(point["x"] - x, 2) + mt.pow(point["y"] - y, 2)) < dist:
            return False
    return True


def generate_coordinates(count, max_x, max_y, min_distance):
    coordinates = []
    i = 0
    while i < count:
        x = rnd.randrange(*max_x)
        y = rnd.randrange(*max_y)
        if has_distance_with_all(coordinates, x, y, min_distance):
            coordinates.append({"x": x, "y": y})
            i += 1
    return coordinates


def argument_check():
    if args.number_of_iterations < 1:
        print("The number of iteration must be greater than 1!")
        exit()
    if args.file_index < 0:
        print("The start file index must be positive!")
        exit()
    if args.number_of_sensors is None or args.number_of_targets is None:
        print("Missing arguments!")
        print("You need to specify the number of sensors (-s option) and targeted points (-t option).")
        exit()
    if args.number_of_targets > args.number_of_sensors:
        print("There must not be more targets than sensors!")
        exit()
    if args.x_max < 0 or args.y_max < 0:
        print("Invalid range parameters!")
        exit()
    if args.lower_bound > args.upper_bound:
        print("The upper bound must be greater then the lower bound!")
        exit()
    if args.lower_bound < 0 or args.lower_bound > 1:
        print("The lower bound must be between 0 and 1!")
        exit()
    if args.upper_bound < 0 or args.upper_bound > 1:
        print("The upper bound must be between 0 and 1!")
        exit()


parser = argparse.ArgumentParser()
parser.add_argument("-i", "--iterations",
                    action="store", type=int, dest="number_of_iterations", default=1,
                    help="the number of the generated networks")
parser.add_argument("-f", "--file index",
                    action="store", type=int, dest="file_index", default=1,
                    help="the index of the start network file")
parser.add_argument("-m1", "--model 1",
                    action="store_true", dest="model_1",
                    help="generate model 1 network")
parser.add_argument("-m2", "--model 2",
                    action="store_true", dest="model_2",
                    help="generate model 2 network")
parser.add_argument("-m1_fix", "--model 1 fix",
                    action="store_true", dest="model_1_fix",
                    help="generate model 1 network with fix scopes")
parser.add_argument("-m2_fix", "--model 2 fix",
                    action="store_true", dest="model_2_fix",
                    help="generate model 2 network with fix power levels")
parser.add_argument("-s_fix", "--fix scope",
                    action="store", type=int, dest="fix_scope", default=120,
                    help="the fix scope for model 1 fix")
parser.add_argument("-p_fix", "--fix power",
                    action="store", type=int, dest="fix_power", default=300,
                    help="the fix power for model 2 fix")
parser.add_argument("--shared",
                    action="store_true", dest="shared",
                    help="different models will share the target and sensor coordinates")
parser.add_argument("-s", "--number of sensors",
                    action="store", type=int, dest="number_of_sensors",
                    help="the number of the sensors")
parser.add_argument("-t", "--number of targets",
                    action="store", type=int, dest="number_of_targets",
                    help="the number of the targeted points")
parser.add_argument("-x", "--width",
                    action="store", type=int, dest="x_max", default=150,
                    help="the width of the desired territory")
parser.add_argument("-y", "--height",
                    action="store", type=int, dest="y_max", default=150,
                    help="the height of the desired territory")
parser.add_argument("-l", "--lower bound",
                    action="store", type=float, dest="lower_bound", default=0,
                    help="the lower bound of the graph density")
parser.add_argument("-u", "--upper bound",
                    action="store", type=float, dest="upper_bound", default=1,
                    help="the upper bound of the graph density")
parser.add_argument("-p", "--maximum power",
                    action="store", type=int, dest="max_power", default=500,
                    help="the maximum power of a sensor")
parser.add_argument("-mds", "--min distance of sensors",
                    action="store", type=int, dest="min_distance_of_sensors", default=5,
                    help="set the minimum distance between the sensors")
parser.add_argument("-mdt", "--min distance of targets",
                    action="store", type=int, dest="min_distance_of_targets", default=10,
                    help="set the minimum distance between the targets")
args = parser.parse_args()

argument_check()

# Constants
DISCRETE_SCOPES = [120, 109, 92, 75, 58, 41, 25, 7]
POWER_LEVELS = [
    # {"power": 8, "range": 7},
    # {"power": 10, "range": 25},
    # {"power": 11, "range": 41},
    # {"power": 12, "range": 58},
    # {"power": 14, "range": 75},
    # {"power": 15, "range": 92},
    # {"power": 16, "range": 109},
    # {"power": 17, "range": 120}
    {"power": 24, "range": 7},
    {"power": 28, "range": 25},
    {"power": 31, "range": 41},
    {"power": 35, "range": 58},
    {"power": 39, "range": 75},
    {"power": 42, "range": 92},
    {"power": 46, "range": 109},
    {"power": 48, "range": 120}
]

# Init variables
number_of_iterations = args.number_of_iterations  # Number of instances
file_index = args.file_index  # Creating the instance with a desired start index
number_of_sensors = args.number_of_sensors  # Number of sensors
number_of_targets = args.number_of_targets  # Number of the targeted points
x_max = args.x_max
y_max = args.y_max
lower_bound = args.lower_bound
upper_bound = args.upper_bound
fix_scope = args.fix_scope
fix_power = args.fix_power
max_power = args.max_power
min_distance_sensor = args.min_distance_of_sensors
min_distance_target = args.min_distance_of_targets
shared = args.shared
plot = True  # True if you want to generate images

range_x = (5, x_max - 5)  # x Coords
range_y = (5, y_max - 5)  # y Coords

labels = {}
for sensor in range(1, number_of_sensors + 1):
    labels[sensor] = sensor

# Output directory
if not os.path.exists("./out"):
    os.makedirs("./out")
out_dir = "./out/{}/".format(datetime.now().strftime("%m-%d-%Y_%H-%M-%S"))
os.makedirs(out_dir)

if args.model_1:
    os.makedirs(out_dir + "model_1/networks")
    os.makedirs(out_dir + "model_1/data")
if args.model_1_fix:
    os.makedirs(out_dir + "model_1_fix/networks")
    os.makedirs(out_dir + "model_1_fix/data")
if args.model_2:
    os.makedirs(out_dir + "model_2/networks")
    os.makedirs(out_dir + "model_2/data")
if args.model_2_fix:
    os.makedirs(out_dir + "model_2_fix/networks")
    os.makedirs(out_dir + "model_2_fix/data")

current_file = file_index
clean = False
while current_file < file_index + number_of_iterations:
    if clean:
        remove_files_by_index(current_file)
        clean = False
    sensor_coordinates = None
    target_coordinates = None
    if shared:
        sensor_coordinates = generate_coordinates(number_of_sensors, range_x, range_y, min_distance_sensor)
        target_coordinates = generate_coordinates(number_of_targets, range_x, range_y, min_distance_target)
    if args.model_1:
        model = Model1(current_file, "model_1", sensor_coordinates, target_coordinates)
        if not model.generating_network():
            clean = True
            continue
    if args.model_1_fix:
        model = Model1(current_file, "model_1_fix", sensor_coordinates, target_coordinates, True)
        if not model.generating_network():
            clean = True
            continue
    if args.model_2:
        model = Model2(current_file, "model_2", sensor_coordinates, target_coordinates)
        if not model.generating_network():
            clean = True
            continue
    if args.model_2_fix:
        model = Model2(current_file, "model_2_fix", sensor_coordinates, target_coordinates, True)
        if not model.generating_network():
            clean = True
            continue
    print("Current file: " + str(current_file))
    current_file += 1


print("Files generated!")
exit(0)
