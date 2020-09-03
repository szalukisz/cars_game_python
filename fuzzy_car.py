from random import random, randint


from car import *
from util import *
from Fuzzy_System.eval_fis import *


class CarAI_Fuzzy(CarAI):
    def __init__(self, ray_count=None, additional_front_ray_count=None, rays_params=None, *args, **kwargs):
        super(CarAI, self).__init__(*args, **kwargs)
        if rays_params is None and ray_count is None:
            ray_count = randint(3, 9)
            origin = np.zeros((ray_count, 2))
            angle = np.zeros(ray_count)
            length = np.zeros(ray_count)
            for i in range(ray_count):
                angle[i] = random() * 2 * np.pi
                r = random() > .5
                if r:
                    origin[i, 0] = (self.rect[0, 0] - self.pos[0]) * random()
                    origin[i, 1] = self.rect[0, 1] - self.pos[1]
                else:
                    origin[i, 0] = self.rect[0, 0] - self.pos[0]
                    origin[i, 1] = (self.rect[0, 1] - self.pos[1]) * random()

                if 0 < angle[i] <= np.pi / 2:
                    pass
                elif np.pi / 2 < angle[i] <= np.pi:
                    origin[i, 0] *= -1
                elif np.pi < angle[i] <= np.pi * 3 / 2:
                    origin[i, 0] *= -1
                    origin[i, 1] *= -1
                elif np.pi * 3 / 2 < angle[i] <= np.pi:
                    origin[i, 1] *= -1
                length[i] = 63 + 255 * random()
            rays_params = {'origin': origin,
                           'angle': angle,
                           'length': length}
        self.rays_v = True
        super(CarAI_Fuzzy, self).__init__(ray_count=ray_count, additional_front_ray_count=additional_front_ray_count,
                                            rays_params=rays_params, *args, **kwargs)
        self.__score = None
        model_arch = (self._dists.shape[0], 16, 16, 2)
        self.__weights = [np.random.normal(size=(model_arch[i + 1], model_arch[i])) for i in range(len(model_arch) - 1)]
        self.__biases = [np.random.normal(size=(model_arch[i], 1)) for i in range(1, len(model_arch))]

        self.fis = FuzzySystem()

        # _ define L-R input
        self.fis.addInput([-1, 1], Name='L-R')
        self.fis.addMF('L-R', 'trapmf', [-1, -1, -0.15, -0.1], Name='F_left')
        self.fis.addMF('L-R', 'trapmf', [0.1, 0.15, 1, 1], Name='F_right')
        self.fis.addMF('L-R', 'trimf', [-0.2, 0, 0.2], Name='Mid')

        # _ define front ray input
        self.fis.addInput([0, 1], Name='Front')
        self.fis.addMF('Front', 'trapmf', [0, 0, 0.08, 0.15], Name='Close')
        self.fis.addMF('Front', 'trapmf', [0.09, 0.15, 0.40, 0.65], Name='MidRange')
        self.fis.addMF('Front', 'trapmf', [0.25, 0.35, 1, 1], Name='Far')

        # _ turn output
        self.fis.addOutput([-1, 1], Name='turn')
        self.fis.addMF('turn', 'trimf', [-0.1, 0, 0.1], Name="Mid")
        self.fis.addMF('turn', 'trapmf', [-1, -1, -0.7, -0.55], Name='To_left')
        self.fis.addMF('turn', 'trapmf', [0.55, 0.7, 1, 1], Name='To_right')

        # _ move speed output
        self.fis.addOutput([-1, 1], Name='move')
        self.fis.addMF('move', 'trapmf', [0.15, 0.25, 0.35, 0.4], Name='Slow')
        self.fis.addMF('move', 'trapmf', [0.45, 0.55, 0.70, 0.85], Name='Fast')
        self.fis.addMF('move', 'trapmf', [0.85, 0.95, 1, 1], Name='V_fast')
        self.fis.addMF('move', 'trapmf', [-1, -1, -0.5, -0.4], Name='Back')

        # _ each rule [input1, input2, output1, output2, connection(and=1, or=0)]
        ruleList = [[1, 2, 1, 2, 1],
                    [2, 2, 0, 2, 1],
                    [0, 2, 2, 2, 1],
                    [1, 1, 1, 1, 1],
                    [0, 1, 2, 1, 1],
                    [0, 0, 2, 2, 1],
                    [1, 0, 1, 2, 1],
                    [2, 1, 0, 2, 1],
                    [2, 0, 2, 2, 1]]
        self.fis.addRule(ruleList)

    def __setattr__(self, name, value):
        if name == 'score':
            self.__score = value
        super(CarAI_Fuzzy, self).__setattr__(name, value)

    def __getattr__(self, name):
        if name == 'score':
            return self.__score
        return super(CarAI_Fuzzy, self).__getattr__(name)

    def handle_event(self, event):
        pass

    def draw(self, surface):
        updated_rects = []
        if not self.hidden:
            updated_rects.extend(
                super(CarAI_Fuzzy, self).draw(surface, self.rays_v))
        return updated_rects

    def run(self, delta_time, collision_force_dir, track):
        super(CarAI_Fuzzy, self).run(delta_time, collision_force_dir, track)

        result_logic_regression = [0.8, 0.0]

        # _ input: ray distances
        lr_diff = self._dists[2] - self._dists[4]

        output, rul_dis = eval_fis(self.fis, [lr_diff, self._dists[3]], True)

        result_logic_regression[0] = output[1]      # _ move
        result_logic_regression[1] = output[0]      # _ turn

        # _ output: move and turn
        self._move = clamp(output[1], -1, 1)
        self._turn = clamp(output[0], -1, 1)

        # _ printing car status
        # if random() < 0.05:
        #     pass
        #     print("{} {:2.4f} {:2.4f} | {:2.4f}".format(self._dists, output[0], output[1], lr_diff))
        #     print(rul_dis) # rule activations

        super(CarAI, self).run(delta_time, collision_force_dir, track)


class FuzzyAlgorithm(object):
    def __init__(self, race, ray_count=7, additional_front_ray_count=0, population=1):
        self.__race = race
        self.__batch_size = 1
        self.population = population
        self.__cars = [CarAI_Fuzzy(ray_count=ray_count, additional_front_ray_count=additional_front_ray_count)for _ in
                       range(self.population)]

        for car in self.__cars:
            self.__race.add_car(car)
        self.__time = perf_counter()

    def getCar(self):
        return self.__cars[0]
