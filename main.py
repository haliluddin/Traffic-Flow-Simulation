import random
import time
import threading
import pygame
import sys
import os

dflt_green_times = {0: 10, 1: 10, 2: 10, 3: 10}
dflt_red_time = 150
dflt_yellow_time = 5

signal_list = []
signal_count = 4
curr_green_idx = 0
next_green_idx = (curr_green_idx + 1) % signal_count
curr_yellow_flag = 0

speed_map = {'car': 2.25, 'bus': 1.8, 'truck': 1.8, 'bike': 2.5}

spawn_x = {
    'right': [0, 0, 0],
    'down': [755, 727, 697],
    'left': [1400, 1400, 1400],
    'up': [602, 627, 657]
}
spawn_y = {
    'right': [348, 370, 398],
    'down': [0, 0, 0],
    'left': [498, 466, 436],
    'up': [800, 800, 800]
}

lane_vehicles = {
    'right': {0: [], 1: [], 2: [], 'crossed': 0},
    'down':  {0: [], 1: [], 2: [], 'crossed': 0},
    'left':  {0: [], 1: [], 2: [], 'crossed': 0},
    'up':    {0: [], 1: [], 2: [], 'crossed': 0}
}

veh_type_lookup = {0: 'car', 1: 'bus', 2: 'truck', 3: 'bike'}
dir_idx_lookup = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}

signal_draw_coords = [(550, 235), (795, 235), (805, 567), (543, 567)]
timer_draw_coords = [(552, 210), (797, 210), (807, 540), (545, 540)]

stop_line_pos = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
default_stop_pos = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

gap_stopped = 25
gap_moving = 25

allowed_types = {'car': True, 'bus': True, 'truck': True, 'bike': True}
allowed_type_indices = []

turned_vehicles = {'right': {1: [], 2: []}, 'down': {1: [], 2: []},
                   'left': {1: [], 2: []}, 'up': {1: [], 2: []}}
not_turned_vehicles = {'right': {1: [], 2: []}, 'down': {1: [], 2: []},
                       'left': {1: [], 2: []}, 'up': {1: [], 2: []}}

rotation_step = 3
turn_midpoint = {
    'right': {'x': 705, 'y': 445},
    'down':  {'x': 695, 'y': 450},
    'left':  {'x': 695, 'y': 425},
    'up':    {'x': 695, 'y': 400}
}

use_random_green = False
rand_green_range = [10, 20]

elapsed_time = 0
max_sim_time = 300
time_draw_coords = (1100, 50)

pygame.init()
all_vehicles_group = pygame.sprite.Group()


class TS:
    def __init__(self, red_dur, yellow_dur, green_dur):
        self.red_dur = red_dur
        self.yellow_dur = yellow_dur
        self.green_dur = green_dur
        self.display_text = ""


class Vhcl(pygame.sprite.Sprite):
    def __init__(self, lane_idx, veh_type, dir_idx, dir_name, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.lane_idx = lane_idx
        self.veh_type = veh_type
        self.speed = speed_map[veh_type]
        self.dir_idx = dir_idx
        self.dir_name = dir_name
        self.x = spawn_x[dir_name][lane_idx]
        self.y = spawn_y[dir_name][lane_idx]
        self.has_crossed = 0
        self.will_turn = will_turn
        self.did_turn = 0
        self.rotate_angle = 0

        lane_vehicles[dir_name][lane_idx].append(self)
        self.queue_index = len(lane_vehicles[dir_name][lane_idx]) - 1
        self.crossed_queue_index = 0

        img_path = f"images/{dir_name}/{veh_type}.png"
        self.orig_image = pygame.image.load(img_path)
        self.image = pygame.image.load(img_path)

        if len(lane_vehicles[dir_name][lane_idx]) > 1 and \
           lane_vehicles[dir_name][lane_idx][self.queue_index - 1].has_crossed == 0:
            prev = lane_vehicles[dir_name][lane_idx][self.queue_index - 1]
            if dir_name == 'right':
                self.stop_pos = prev.stop_pos - prev.image.get_rect().width - gap_stopped
            elif dir_name == 'left':
                self.stop_pos = prev.stop_pos + prev.image.get_rect().width + gap_stopped
            elif dir_name == 'down':
                self.stop_pos = prev.stop_pos - prev.image.get_rect().height - gap_stopped
            elif dir_name == 'up':
                self.stop_pos = prev.stop_pos + prev.image.get_rect().height + gap_stopped
        else:
            self.stop_pos = default_stop_pos[dir_name]

        if dir_name == 'right':
            offset = self.image.get_rect().width + gap_stopped
            spawn_x[dir_name][lane_idx] -= offset
        elif dir_name == 'left':
            offset = self.image.get_rect().width + gap_stopped
            spawn_x[dir_name][lane_idx] += offset
        elif dir_name == 'down':
            offset = self.image.get_rect().height + gap_stopped
            spawn_y[dir_name][lane_idx] -= offset
        elif dir_name == 'up':
            offset = self.image.get_rect().height + gap_stopped
            spawn_y[dir_name][lane_idx] += offset

        all_vehicles_group.add(self)

    def render(self, surface):
        surface.blit(self.image, (self.x, self.y))

    def move(self):
        dname = self.dir_name
        sline = stop_line_pos[dname]

        if self.has_crossed == 0:
            if dname == 'right' and self.x + self.image.get_rect().width > sline:
                self.has_crossed = 1
                if self.will_turn == 0:
                    not_turned_vehicles[dname][self.lane_idx].append(self)
                    self.crossed_queue_index = len(not_turned_vehicles[dname][self.lane_idx]) - 1
            elif dname == 'down' and self.y + self.image.get_rect().height > sline:
                self.has_crossed = 1
                if self.will_turn == 0:
                    not_turned_vehicles[dname][self.lane_idx].append(self)
                    self.crossed_queue_index = len(not_turned_vehicles[dname][self.lane_idx]) - 1
            elif dname == 'left' and self.x < sline:
                self.has_crossed = 1
                if self.will_turn == 0:
                    not_turned_vehicles[dname][self.lane_idx].append(self)
                    self.crossed_queue_index = len(not_turned_vehicles[dname][self.lane_idx]) - 1
            elif dname == 'up' and self.y < sline:
                self.has_crossed = 1
                if self.will_turn == 0:
                    not_turned_vehicles[dname][self.lane_idx].append(self)
                    self.crossed_queue_index = len(not_turned_vehicles[dname][self.lane_idx]) - 1

        if self.will_turn == 1:
            if dname == 'right':
                self._move_turn_right()
            elif dname == 'down':
                self._move_turn_down()
            elif dname == 'left':
                self._move_turn_left()
            elif dname == 'up':
                self._move_turn_up()
        else:
            self._move_straight()

    def _move_straight(self):
        dname = self.dir_name
        sline = stop_line_pos[dname]

        if dname == 'right':
            if self.has_crossed == 0:
                can_move = ((self.x + self.image.get_rect().width <= self.stop_pos or
                             (curr_green_idx == 0 and curr_yellow_flag == 0)) and
                            (self.queue_index == 0 or
                             self.x + self.image.get_rect().width < (
                                 lane_vehicles[dname][self.lane_idx][self.queue_index - 1].x - gap_moving)))
                if can_move:
                    self.x += self.speed
            else:
                prev_not_turned = not_turned_vehicles[dname][self.lane_idx]
                if (self.crossed_queue_index == 0 or
                    self.x + self.image.get_rect().width < (
                        prev_not_turned[self.crossed_queue_index - 1].x - gap_moving)):
                    self.x += self.speed

        elif dname == 'down':
            if self.has_crossed == 0:
                can_move = ((self.y + self.image.get_rect().height <= self.stop_pos or
                             (curr_green_idx == 1 and curr_yellow_flag == 0)) and
                            (self.queue_index == 0 or
                             self.y + self.image.get_rect().height < (
                                 lane_vehicles[dname][self.lane_idx][self.queue_index - 1].y - gap_moving)))
                if can_move:
                    self.y += self.speed
            else:
                prev_not_turned = not_turned_vehicles[dname][self.lane_idx]
                if (self.crossed_queue_index == 0 or
                    self.y + self.image.get_rect().height < (
                        prev_not_turned[self.crossed_queue_index - 1].y - gap_moving)):
                    self.y += self.speed

        elif dname == 'left':
            if self.has_crossed == 0:
                can_move = ((self.x >= self.stop_pos or
                             (curr_green_idx == 2 and curr_yellow_flag == 0)) and
                            (self.queue_index == 0 or
                             self.x > (
                                 lane_vehicles[dname][self.lane_idx][self.queue_index - 1].x +
                                 lane_vehicles[dname][self.lane_idx][self.queue_index - 1].image.get_rect().width + gap_moving)))
                if can_move:
                    self.x -= self.speed
            else:
                prev_not_turned = not_turned_vehicles[dname][self.lane_idx]
                if (self.crossed_queue_index == 0 or
                    self.x > (
                        prev_not_turned[self.crossed_queue_index - 1].x +
                        prev_not_turned[self.crossed_queue_index - 1].image.get_rect().width + gap_moving)):
                    self.x -= self.speed

        elif dname == 'up':
            if self.has_crossed == 0:
                can_move = ((self.y >= self.stop_pos or
                             (curr_green_idx == 3 and curr_yellow_flag == 0)) and
                            (self.queue_index == 0 or
                             self.y > (
                                 lane_vehicles[dname][self.lane_idx][self.queue_index - 1].y +
                                 lane_vehicles[dname][self.lane_idx][self.queue_index - 1].image.get_rect().height + gap_moving)))
                if can_move:
                    self.y -= self.speed
            else:
                prev_not_turned = not_turned_vehicles[dname][self.lane_idx]
                if (self.crossed_queue_index == 0 or
                    self.y > (
                        prev_not_turned[self.crossed_queue_index - 1].y +
                        prev_not_turned[self.crossed_queue_index - 1].image.get_rect().height + gap_moving)):
                    self.y -= self.speed

    def _move_turn_right(self):
        lane = self.lane_idx
        dname = 'right'
        sline = stop_line_pos[dname]
        midpoint_x = turn_midpoint[dname]['x']

        if lane == 1:
            if self.has_crossed == 0 or (self.x + self.image.get_rect().width < sline + 40):
                can_move = ((self.x + self.image.get_rect().width <= self.stop_pos or
                             (curr_green_idx == 0 and curr_yellow_flag == 0) or
                             self.has_crossed == 1) and
                            (self.queue_index == 0 or
                             self.x + self.image.get_rect().width < (
                                 lane_vehicles[dname][lane][self.queue_index - 1].x - gap_moving) or
                             lane_vehicles[dname][lane][self.queue_index - 1].did_turn == 1))
                if can_move:
                    self.x += self.speed
            else:
                if self.did_turn == 0:
                    self.rotate_angle += rotation_step
                    self.image = pygame.transform.rotate(self.orig_image, self.rotate_angle)
                    self.x += 2.4
                    self.y -= 2.8
                    if self.rotate_angle == 90:
                        self.did_turn = 1
                        turned_vehicles[dname][lane].append(self)
                        self.crossed_queue_index = len(turned_vehicles[dname][lane]) - 1
                else:
                    prev_turned = turned_vehicles[dname][lane]
                    if (self.crossed_queue_index == 0 or
                        self.y > (
                            prev_turned[self.crossed_queue_index - 1].y +
                            prev_turned[self.crossed_queue_index - 1].image.get_rect().height + gap_moving)):
                        self.y -= self.speed

        elif lane == 2:
            if self.has_crossed == 0 or (self.x + self.image.get_rect().width < midpoint_x):
                can_move = ((self.x + self.image.get_rect().width <= self.stop_pos or
                             (curr_green_idx == 0 and curr_yellow_flag == 0) or
                             self.has_crossed == 1) and
                            (self.queue_index == 0 or
                             self.x + self.image.get_rect().width < (
                                 lane_vehicles[dname][lane][self.queue_index - 1].x - gap_moving) or
                             lane_vehicles[dname][lane][self.queue_index - 1].did_turn == 1))
                if can_move:
                    self.x += self.speed
            else:
                if self.did_turn == 0:
                    self.rotate_angle += rotation_step
                    self.image = pygame.transform.rotate(self.orig_image, -self.rotate_angle)
                    self.x += 2
                    self.y += 1.8
                    if self.rotate_angle == 90:
                        self.did_turn = 1
                        turned_vehicles[dname][lane].append(self)
                        self.crossed_queue_index = len(turned_vehicles[dname][lane]) - 1
                else:
                    prev_turned = turned_vehicles[dname][lane]
                    if (self.crossed_queue_index == 0 or
                        (self.y + self.image.get_rect().height) < (
                            prev_turned[self.crossed_queue_index - 1].y - gap_moving)):
                        self.y += self.speed

        else:
            super_vehicle_group = not_turned_vehicles[dname][self.lane_idx]
            if self.has_crossed == 0:
                can_move = ((self.x + self.image.get_rect().width <= self.stop_pos or
                             (curr_green_idx == 0 and curr_yellow_flag == 0)) and
                            (self.queue_index == 0 or
                             self.x + self.image.get_rect().width < (
                                 lane_vehicles[dname][self.lane_idx][self.queue_index - 1].x - gap_moving)))
                if can_move:
                    self.x += self.speed
            else:
                if (self.crossed_queue_index == 0 or
                    self.x + self.image.get_rect().width < (
                        super_vehicle_group[self.crossed_queue_index - 1].x - gap_moving)):
                    self.x += self.speed

    def _move_turn_down(self):
        lane = self.lane_idx
        dname = 'down'
        sline = stop_line_pos[dname]
        midpoint_y = turn_midpoint[dname]['y']

        if lane == 1:
            if self.has_crossed == 0 or (self.y + self.image.get_rect().height < sline + 50):
                can_move = ((self.y + self.image.get_rect().height <= self.stop_pos or
                             (curr_green_idx == 1 and curr_yellow_flag == 0) or
                             self.has_crossed == 1) and
                            (self.queue_index == 0 or
                             self.y + self.image.get_rect().height < (
                                 lane_vehicles[dname][lane][self.queue_index - 1].y - gap_moving) or
                             lane_vehicles[dname][lane][self.queue_index - 1].did_turn == 1))
                if can_move:
                    self.y += self.speed
            else:
                if self.did_turn == 0:
                    self.rotate_angle += rotation_step
                    self.image = pygame.transform.rotate(self.orig_image, self.rotate_angle)
                    self.x += 1.2
                    self.y += 1.8
                    if self.rotate_angle == 90:
                        self.did_turn = 1
                        turned_vehicles[dname][lane].append(self)
                        self.crossed_queue_index = len(turned_vehicles[dname][lane]) - 1
                else:
                    prev_turned = turned_vehicles[dname][lane]
                    if (self.crossed_queue_index == 0 or
                        (self.x + self.image.get_rect().width) < (
                            prev_turned[self.crossed_queue_index - 1].x - gap_moving)):
                        self.x += self.speed

        elif lane == 2:
            if self.has_crossed == 0 or (self.y + self.image.get_rect().height < midpoint_y):
                can_move = ((self.y + self.image.get_rect().height <= self.stop_pos or
                             (curr_green_idx == 1 and curr_yellow_flag == 0) or
                             self.has_crossed == 1) and
                            (self.queue_index == 0 or
                             self.y + self.image.get_rect().height < (
                                 lane_vehicles[dname][lane][self.queue_index - 1].y - gap_moving) or
                             lane_vehicles[dname][lane][self.queue_index - 1].did_turn == 1))
                if can_move:
                    self.y += self.speed
            else:
                if self.did_turn == 0:
                    self.rotate_angle += rotation_step
                    self.image = pygame.transform.rotate(self.orig_image, -self.rotate_angle)
                    self.x -= 2.5
                    self.y += 2
                    if self.rotate_angle == 90:
                        self.did_turn = 1
                        turned_vehicles[dname][lane].append(self)
                        self.crossed_queue_index = len(turned_vehicles[dname][lane]) - 1
                else:
                    prev_turned = turned_vehicles[dname][lane]
                    if (self.crossed_queue_index == 0 or
                        self.x > (
                            prev_turned[self.crossed_queue_index - 1].x +
                            prev_turned[self.crossed_queue_index - 1].image.get_rect().width + gap_moving)):
                        self.x -= self.speed

        else:
            super_vehicle_group = not_turned_vehicles[dname][self.lane_idx]
            if self.has_crossed == 0:
                can_move = ((self.y + self.image.get_rect().height <= self.stop_pos or
                             (curr_green_idx == 1 and curr_yellow_flag == 0)) and
                            (self.queue_index == 0 or
                             self.y + self.image.get_rect().height < (
                                 lane_vehicles[dname][self.lane_idx][self.queue_index - 1].y - gap_moving)))
                if can_move:
                    self.y += self.speed
            else:
                if (self.crossed_queue_index == 0 or
                    self.y + self.image.get_rect().height < (
                        super_vehicle_group[self.crossed_queue_index - 1].y - gap_moving)):
                    self.y += self.speed

    def _move_turn_left(self):
        lane = self.lane_idx
        dname = 'left'
        sline = stop_line_pos[dname]
        midpoint_x = turn_midpoint[dname]['x']

        if lane == 1:
            if self.has_crossed == 0 or (self.x > sline - 70):
                can_move = ((self.x >= self.stop_pos or
                             (curr_green_idx == 2 and curr_yellow_flag == 0) or
                             self.has_crossed == 1) and
                            (self.queue_index == 0 or
                             self.x > (
                                 lane_vehicles[dname][lane][self.queue_index - 1].x +
                                 lane_vehicles[dname][lane][self.queue_index - 1].image.get_rect().width + gap_moving) or
                             lane_vehicles[dname][lane][self.queue_index - 1].did_turn == 1))
                if can_move:
                    self.x -= self.speed
            else:
                if self.did_turn == 0:
                    self.rotate_angle += rotation_step
                    self.image = pygame.transform.rotate(self.orig_image, self.rotate_angle)
                    self.x -= 1
                    self.y += 1.2
                    if self.rotate_angle == 90:
                        self.did_turn = 1
                        turned_vehicles[dname][lane].append(self)
                        self.crossed_queue_index = len(turned_vehicles[dname][lane]) - 1
                else:
                    prev_turned = turned_vehicles[dname][lane]
                    if (self.crossed_queue_index == 0 or
                        (self.y + self.image.get_rect().height) < (
                            prev_turned[self.crossed_queue_index - 1].y - gap_moving)):
                        self.y += self.speed

        elif lane == 2:
            if self.has_crossed == 0 or (self.x > midpoint_x):
                can_move = ((self.x >= self.stop_pos or
                             (curr_green_idx == 2 and curr_yellow_flag == 0) or
                             self.has_crossed == 1) and
                            (self.queue_index == 0 or
                             self.x > (
                                 lane_vehicles[dname][lane][self.queue_index - 1].x +
                                 lane_vehicles[dname][lane][self.queue_index - 1].image.get_rect().width + gap_moving) or
                             lane_vehicles[dname][lane][self.queue_index - 1].did_turn == 1))
                if can_move:
                    self.x -= self.speed
            else:
                if self.did_turn == 0:
                    self.rotate_angle += rotation_step
                    self.image = pygame.transform.rotate(self.orig_image, -self.rotate_angle)
                    self.x -= 1.8
                    self.y -= 2.5
                    if self.rotate_angle == 90:
                        self.did_turn = 1
                        turned_vehicles[dname][lane].append(self)
                        self.crossed_queue_index = len(turned_vehicles[dname][lane]) - 1
                else:
                    prev_turned = turned_vehicles[dname][lane]
                    if (self.crossed_queue_index == 0 or
                        self.y > (
                            prev_turned[self.crossed_queue_index - 1].y +
                            prev_turned[self.crossed_queue_index - 1].image.get_rect().height + gap_moving)):
                        self.y -= self.speed

        else:
            super_vehicle_group = not_turned_vehicles[dname][self.lane_idx]
            if self.has_crossed == 0:
                can_move = ((self.x >= self.stop_pos or
                             (curr_green_idx == 2 and curr_yellow_flag == 0)) and
                            (self.queue_index == 0 or
                             self.x > (
                                 lane_vehicles[dname][self.lane_idx][self.queue_index - 1].x +
                                 lane_vehicles[dname][self.lane_idx][self.queue_index - 1].image.get_rect().width + gap_moving)))
                if can_move:
                    self.x -= self.speed
            else:
                if (self.crossed_queue_index == 0 or
                    self.x > (
                        super_vehicle_group[self.crossed_queue_index - 1].x +
                        super_vehicle_group[self.crossed_queue_index - 1].image.get_rect().width + gap_moving)):
                    self.x -= self.speed

    def _move_turn_up(self):
        lane = self.lane_idx
        dname = 'up'
        sline = stop_line_pos[dname]
        midpoint_y = turn_midpoint[dname]['y']

        if lane == 1:
            if self.has_crossed == 0 or (self.y > sline - 60):
                can_move = ((self.y >= self.stop_pos or
                             (curr_green_idx == 3 and curr_yellow_flag == 0) or
                             self.has_crossed == 1) and
                            (self.queue_index == 0 or
                             self.y > (
                                 lane_vehicles[dname][lane][self.queue_index - 1].y +
                                 lane_vehicles[dname][lane][self.queue_index - 1].image.get_rect().height + gap_moving) or
                             lane_vehicles[dname][lane][self.queue_index - 1].did_turn == 1))
                if can_move:
                    self.y -= self.speed
            else:
                if self.did_turn == 0:
                    self.rotate_angle += rotation_step
                    self.image = pygame.transform.rotate(self.orig_image, self.rotate_angle)
                    self.x -= 2
                    self.y -= 1.2
                    if self.rotate_angle == 90:
                        self.did_turn = 1
                        turned_vehicles[dname][lane].append(self)
                        self.crossed_queue_index = len(turned_vehicles[dname][lane]) - 1
                else:
                    prev_turned = turned_vehicles[dname][lane]
                    if (self.crossed_queue_index == 0 or
                        self.x > (
                            prev_turned[self.crossed_queue_index - 1].x +
                            prev_turned[self.crossed_queue_index - 1].image.get_rect().width + gap_moving)):
                        self.x -= self.speed

        elif lane == 2:
            if self.has_crossed == 0 or (self.y > midpoint_y):
                can_move = ((self.y >= self.stop_pos or
                             (curr_green_idx == 3 and curr_yellow_flag == 0) or
                             self.has_crossed == 1) and
                            (self.queue_index == 0 or
                             self.y > (
                                 lane_vehicles[dname][lane][self.queue_index - 1].y +
                                 lane_vehicles[dname][lane][self.queue_index - 1].image.get_rect().height + gap_moving) or
                             lane_vehicles[dname][lane][self.queue_index - 1].did_turn == 1))
                if can_move:
                    self.y -= self.speed
            else:
                if self.did_turn == 0:
                    self.rotate_angle += rotation_step
                    self.image = pygame.transform.rotate(self.orig_image, -self.rotate_angle)
                    self.x += 1
                    self.y -= 1
                    if self.rotate_angle == 90:
                        self.did_turn = 1
                        turned_vehicles[dname][lane].append(self)
                        self.crossed_queue_index = len(turned_vehicles[dname][lane]) - 1
                else:
                    prev_turned = turned_vehicles[dname][lane]
                    if (self.crossed_queue_index == 0 or
                        self.x < (
                            prev_turned[self.crossed_queue_index - 1].x -
                            prev_turned[self.crossed_queue_index - 1].image.get_rect().width - gap_moving)):
                        self.x += self.speed

        else:
            super_vehicle_group = not_turned_vehicles[dname][self.lane_idx]
            if self.has_crossed == 0:
                can_move = ((self.y >= self.stop_pos or
                             (curr_green_idx == 3 and curr_yellow_flag == 0)) and
                            (self.queue_index == 0 or
                             self.y > (
                                 lane_vehicles[dname][self.lane_idx][self.queue_index - 1].y +
                                 lane_vehicles[dname][self.lane_idx][self.queue_index - 1].image.get_rect().height + gap_moving)))
                if can_move:
                    self.y -= self.speed
            else:
                if (self.crossed_queue_index == 0 or
                    self.y > (
                        super_vehicle_group[self.crossed_queue_index - 1].y +
                        super_vehicle_group[self.crossed_queue_index - 1].image.get_rect().height + gap_moving)):
                    self.y -= self.speed


def init_signals():
    min_rand, max_rand = rand_green_range
    if use_random_green:
        s1 = TS(0, dflt_yellow_time, random.randint(min_rand, max_rand))
        signal_list.append(s1)
        s2 = TS(s1.red_dur + s1.yellow_dur + s1.green_dur, dflt_yellow_time, random.randint(min_rand, max_rand))
        signal_list.append(s2)
        s3 = TS(dflt_red_time, dflt_yellow_time, random.randint(min_rand, max_rand))
        signal_list.append(s3)
        s4 = TS(dflt_red_time, dflt_yellow_time, random.randint(min_rand, max_rand))
        signal_list.append(s4)
    else:
        s1 = TS(0, dflt_yellow_time, dflt_green_times[0])
        signal_list.append(s1)
        s2 = TS(s1.yellow_dur + s1.green_dur, dflt_yellow_time, dflt_green_times[1])
        signal_list.append(s2)
        s3 = TS(dflt_red_time, dflt_yellow_time, dflt_green_times[2])
        signal_list.append(s3)
        s4 = TS(dflt_red_time, dflt_yellow_time, dflt_green_times[3])
        signal_list.append(s4)

    cycle_signals()


def print_signal_status():
    for idx in range(signal_count):
        sig = signal_list[idx]
        if idx == curr_green_idx:
            if curr_yellow_flag == 0:
                print(f" GREEN SIG {idx+1} -> r:{sig.red_dur} y:{sig.yellow_dur} g:{sig.green_dur}")
            else:
                print(f"YELLOW SIG {idx+1} -> r:{sig.red_dur} y:{sig.yellow_dur} g:{sig.green_dur}")
        else:
            print(f"   RED SIG {idx+1} -> r:{sig.red_dur} y:{sig.yellow_dur} g:{sig.green_dur}")
    print()


def cycle_signals():
    global curr_green_idx, curr_yellow_flag, next_green_idx

    while signal_list[curr_green_idx].green_dur > 0:
        print_signal_status()
        decrement_signals()
        time.sleep(1)

    curr_yellow_flag = 1
    for ln in range(3):
        for v in lane_vehicles[dir_idx_lookup[curr_green_idx]][ln]:
            v.stop_pos = default_stop_pos[dir_idx_lookup[curr_green_idx]]

    while signal_list[curr_green_idx].yellow_dur > 0:
        print_signal_status()
        decrement_signals()
        time.sleep(1)

    curr_yellow_flag = 0

    if use_random_green:
        signal_list[curr_green_idx].green_dur = random.randint(rand_green_range[0], rand_green_range[1])
    else:
        signal_list[curr_green_idx].green_dur = dflt_green_times[curr_green_idx]
    signal_list[curr_green_idx].yellow_dur = dflt_yellow_time
    signal_list[curr_green_idx].red_dur = dflt_red_time

    curr_green_idx = next_green_idx
    next_green_idx = (curr_green_idx + 1) % signal_count
    signal_list[next_green_idx].red_dur = signal_list[curr_green_idx].yellow_dur + signal_list[curr_green_idx].green_dur

    cycle_signals()


def decrement_signals():
    for idx in range(signal_count):
        sig = signal_list[idx]
        if idx == curr_green_idx:
            if curr_yellow_flag == 0:
                sig.green_dur -= 1
            else:
                sig.yellow_dur -= 1
        else:
            sig.red_dur -= 1


def spawn_vehicles_continuous():
    while True:
        vt_idx = random.choice(allowed_type_indices)
        ln_idx = random.randint(1, 2)
        will_turn_flag = 0

        if ln_idx in [1, 2]:
            if random.randint(0, 99) < 40:
                will_turn_flag = 1

        tmp = random.randint(0, 99)
        direction_choice = 0
        dist_breaks = [25, 50, 75, 100]
        if tmp < dist_breaks[0]:
            direction_choice = 0
        elif tmp < dist_breaks[1]:
            direction_choice = 1
        elif tmp < dist_breaks[2]:
            direction_choice = 2
        else:
            direction_choice = 3

        Vhcl(ln_idx, veh_type_lookup[vt_idx], direction_choice, dir_idx_lookup[direction_choice], will_turn_flag)
        time.sleep(1)


def track_simulation_time():
    global elapsed_time, max_sim_time
    while True:
        elapsed_time += 1
        time.sleep(1)
        if elapsed_time == max_sim_time:
            os._exit(1)


class MainApp:
    _idx_counter = 0
    for vt_name, is_allowed in allowed_types.items():
        if is_allowed:
            allowed_type_indices.append(_idx_counter)
        _idx_counter += 1

    t_init = threading.Thread(target=init_signals, name="signal_init")
    t_init.daemon = True
    t_init.start()

    black = (0, 0, 0)
    white = (255, 255, 255)
    win_width, win_height = 1400, 800
    window = pygame.display.set_mode((win_width, win_height))
    pygame.display.set_caption("TRAFFIC SIMULATION")

    bg_image = pygame.image.load('images/intersection.png')
    red_img = pygame.image.load('images/signals/red.png')
    yellow_img = pygame.image.load('images/signals/yellow.png')
    green_img = pygame.image.load('images/signals/green.png')
    font_obj = pygame.font.Font(None, 40)

    t_spawn = threading.Thread(target=spawn_vehicles_continuous, name="vehicle_spawn")
    t_spawn.daemon = True
    t_spawn.start()

    t_time = threading.Thread(target=track_simulation_time, name="time_tracker")
    t_time.daemon = True
    t_time.start()

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                sys.exit()

        window.blit(bg_image, (0, 0))

        for idx in range(signal_count):
            sig = signal_list[idx]
            if idx == curr_green_idx:
                if curr_yellow_flag == 1:
                    sig.display_text = f"{sig.yellow_dur:02d}"
                    window.blit(yellow_img, signal_draw_coords[idx])
                else:
                    sig.display_text = f"{sig.green_dur:02d}"
                    window.blit(green_img, signal_draw_coords[idx])
            else:
                if sig.red_dur <= 10:
                    sig.display_text = f"{sig.red_dur:02d}"
                else:
                    sig.display_text = "00"
                window.blit(red_img, signal_draw_coords[idx])

        for idx in range(signal_count):
            txt = font_obj.render(signal_list[idx].display_text, True, white, black)
            window.blit(txt, timer_draw_coords[idx])

        time_txt = font_obj.render(f"Time: {elapsed_time}", True, white, black)
        window.blit(time_txt, time_draw_coords)

        for v in all_vehicles_group:
            window.blit(v.image, [v.x, v.y])
            v.move()

        pygame.display.update()
