""" Toro
| Copyright (C) 2019 TU Braunschweig, Institute for Computer and Network Engineering
| All rights reserved.
| See LICENSE file for copyright and license details.

:Authors:
         - Leonie Koehler
         - Nikolas Brendes

Description
-----------
This modules provides plotting functions (interval diagram, reachability graph, summary graph).  
"""

from pycpa import model
import xml.etree.ElementTree as xml
import math
import copy



class draw_read_data_intervals(object):
    """ Initialize a new Image\n

        Optional:
        max_data_age = all | first | last | none\n
        robustness_margin = all | first | last | none\n
        dependency_polygon = True | False 
    """ 
    CRED = '\033[91m'
    CEND = '\033[0m'
    __scale = 10
    __off_x_g = 20
    # Number of Extra Periods after Hyperperiod
    __period_scale = 4

    def __init__(self, chain_results, dependency_polygon = False, robustness_margin = "none", max_data_age = "none"):
        
        self.__chain_results = chain_results
        self.__cut_periods = 0

        width , height = self.__calc_img_size()
        self.__img = image("test", width, height)

        self._draw_read_data_intervals()
        self._draw_x_axis()
        
        self.draw_dependency_polygon(dependency_polygon)
        self.draw_robustness_margins(robustness_margin)
        self.draw_max_data_age(max_data_age)

        

    def __calc_img_size(self):
        # search Task with the longest Period
        self.__longest_period = 0
        for p in self.__chain_results.path_matrix[-1]:
            if p.period > self.__longest_period:
                self.__longest_period = p.period
        # calculate width and height of the Image
        width = int(self.__scale * ( self.__chain_results.hyperperiod + self.__period_scale * self.__longest_period) + self.__off_x_g * 2)
        height = len(self.__chain_results.path_matrix[0]) * 200 + 100

        if self.__chain_results.hyperperiod / self.__longest_period > 16:
            self.__cut_periods = self.__chain_results.hyperperiod / self.__longest_period - 4
        return (width, height)

    def save_file(self, file_name="draw_chain_no_filename.svg"):
        width , height = self.__calc_img_size()
        
        # Sort the Elements in the Image, so they overlap correctly
        for c in self.__img.root.getchildren():
            if c.tag == "line":
                self.__img.root.remove(c)
                self.__img.root.insert(0,c)
                
        for c in self.__img.root.getchildren():
            if c.tag == "polygon":
                if c.get("name") == "robustness_margin":
                    self.__img.root.remove(c)
                    self.__img.root.insert(0,c)
        for c in self.__img.root.getchildren():
            if c.tag == "polygon":
                if c.get("name") == "max_data_age":
                    self.__img.root.remove(c)
                    self.__img.root.insert(0,c)
        for c in self.__img.root.getchildren():
            if c.tag == "polygon":
                if c.get("name") == "dependency_polygon":
                    self.__img.root.remove(c)
                    self.__img.root.insert(0,c)
    
        # Add a white background
        background = xml.Element("rect", x = "0", y = "0", width = str(width), height = str(height), style = "fill:white;")
        self.__img.root.insert(0,background)

        # Save the image
        tree = xml.ElementTree(self.__img.root)
        #tree.write(str(file_name))
        if len(str(file_name)) > 4:
            if str(file_name)[-4:] == ".svg":
                tree.write(str(file_name))
            else:
                tree.write(str(file_name) + ".svg")
        else:
            tree.write(str(file_name) + ".svg")
  
    def _draw_read_data_intervals(self):
        off_y = 50

        t_end = self.__chain_results.hyperperiod + self.__longest_period * self.__period_scale

        for task in self.__chain_results.job_matrix:
            # Draw Task Name
            self.__img._text("TASK: "+task[0].name[:-2]+"   Period: "+str(task[0].period), self.__off_x_g + 130 , off_y - 30,"font: bold 18px sans-serif;")
            i = 0
            for job in task:
                i += 1
                # Draw Read Interval
                modulus = (job.Rmax - job.Rmin) / job.period + 1
                height = 30 / modulus
                self.__img._line(     self.__off_x_g + job.Rmin * self.__scale, off_y + ((job.job_number - 1) % modulus) * height, self.__off_x_g + job.Rmax * self.__scale, off_y + ((job.job_number - 1) % modulus) * height, "blue")
                self.__img._text("RI",self.__off_x_g + (job.Rmin + (job.Rmax - job.Rmin) / 2) * self.__scale, off_y - 8 + ((job.job_number - 1) % modulus) * height)
                self.__img._circle(self.__off_x_g + job.Rmin * self.__scale, off_y + ((job.job_number - 1) % modulus) * height, 4, "fill: blue; stroke: blue; stroke-width: 2;", id = "Rmin_" + job.name)
                self.__img._circle(self.__off_x_g + job.Rmax * self.__scale, off_y + ((job.job_number - 1) % modulus) * height, 4, "fill: blue; stroke: blue; stroke-width: 2;", id = "Rmax_" + job.name)

                # Draw Data Interval
                
                modulus = (job.Dmax - job.Dmin) / job.period + 1
                height = 50 / modulus
                self.__img._line(self.__off_x_g + job.Dmin * self.__scale, off_y + 45 + ((job.job_number - 1) % modulus) * height, self.__off_x_g + job.Dmax * self.__scale, off_y + 45 + ((job.job_number - 1) % modulus) * height, "green")
                self.__img._text("DI",self.__off_x_g + (job.Dmin + (job.Dmax - job.Dmin) / 2) * self.__scale, off_y + 38 + ((job.job_number - 1) % modulus) * height)
                self.__img._circle(self.__off_x_g + job.Dmin * self.__scale, off_y + 45 + ((job.job_number - 1) % modulus) * height, 4, "fill: green; stroke: green; stroke-width: 2;", id = "Dmin_" + job.name)
                self.__img._circle(self.__off_x_g + job.Dmax * self.__scale, off_y + 45 + ((job.job_number - 1) % modulus) * height, 4, "fill: white; stroke: green; stroke-width: 2;", id = "Dmax_" + job.name)

                # Draw Job Number
                self.__img._text_circle(str(job.job_number),self.__off_x_g + (job.period * (job.job_number - 1) + job.period / 2) * self.__scale, off_y + 110)

                # Draw wcet
                #self.__img._line(self.__off_x_g + job.Rmax * self.__scale, off_y + 8, self.__off_x_g + (job.Rmax + job.wcet) * self.__scale, off_y + 8, "grey")
                
                # Draw wcrt
                #self.__img._line(self.__off_x_g + (job.period * (job.job_number - 1)) * self.__scale, off_y + 12, self.__off_x_g + (job.period * (job.job_number - 1) + job.wcrt)* self.__scale, off_y + 12, "black")
                
                #Draw Period
                self.__img._line(self.__off_x_g + (job.period * (job.job_number)) * self.__scale, off_y - 5, self.__off_x_g + (job.period * (job.job_number)) * self.__scale, off_y + 120, "black", 1)


            # Draw more periods than required in the analysis
            i = 0
            job0 = copy.deepcopy(job)
            while job0.period * job0.job_number < t_end:
                i += 1
                job0.Rmin += job0.period
                job0.Rmax += job0.period
                job0.Dmin += job0.period
                job0.Dmax += job0.period
                job0.job_number += 1
                job0.name = job0.name.split(",")[0] + "," +str(job0.job_number)

                modulus = (job.Rmax - job.Rmin) / job.period + 1
                height = 30 / modulus
                self.__img._line(     self.__off_x_g + job0.Rmin * self.__scale, off_y + ((job0.job_number - 1) % modulus) * height, self.__off_x_g + job0.Rmax * self.__scale, off_y + ((job0.job_number - 1) % modulus) * height, "blue")
                self.__img._text("RI",self.__off_x_g + (job0.Rmin + (job0.Rmax - job0.Rmin) / 2) * self.__scale, off_y - 8 + ((job0.job_number - 1) % modulus) * height)
                self.__img._circle(self.__off_x_g + job0.Rmin * self.__scale, off_y + ((job0.job_number - 1) % modulus) * height, 4, "fill: blue; stroke: blue; stroke-width: 2;", id = "Rmin_" + job0.name)
                self.__img._circle(self.__off_x_g + job0.Rmax * self.__scale, off_y + ((job0.job_number - 1) % modulus) * height, 4, "fill: blue; stroke: blue; stroke-width: 2;", id = "Rmax_" + job0.name)

                modulus = (job.Dmax - job.Dmin) / job.period + 1
                height = 50 / modulus
                self.__img._line(self.__off_x_g + job0.Dmin * self.__scale, off_y + 45 + ((job0.job_number - 1) % modulus) * height, self.__off_x_g + job0.Dmax * self.__scale, off_y + 45 + ((job0.job_number - 1) % modulus) * height, "green")
                self.__img._text("DI",self.__off_x_g + (job0.Dmin + (job0.Dmax - job0.Dmin) / 2) * self.__scale, off_y + 38 + ((job0.job_number - 1) % modulus) * height)
                self.__img._circle(self.__off_x_g + job0.Dmin * self.__scale, off_y + 45 + ((job0.job_number - 1) % modulus) * height, 4, "fill: green; stroke: green; stroke-width: 2;", id = "Dmin_" + job0.name)
                self.__img._circle(self.__off_x_g + job0.Dmax * self.__scale, off_y + 45 + ((job0.job_number - 1) % modulus) * height, 4, "fill: white; stroke: green; stroke-width: 2;", id = "Dmax_" + job0.name)

                self.__img._text_circle(str(job0.job_number),self.__off_x_g + (job0.period * (job0.job_number - 1) + job0.period / 2) * self.__scale, off_y + 110)

                #Draw Period
                self.__img._line(self.__off_x_g + (job0.period * (job0.job_number)) * self.__scale, off_y - 5, self.__off_x_g + (job0.period * (job0.job_number)) * self.__scale, off_y + 120, "grey", 2)

            off_y += 200

    def _draw_x_axis(self):
        # Number of Taks:
        i = len(self.__chain_results.path_matrix[0])
        
        # X and Y Axis:
        self.__img._line(self.__off_x_g, i * 200 + 50, (self.__chain_results.hyperperiod + self.__longest_period * self.__period_scale) * self.__scale, i * 200 + 50, "black", 3)
        self.__img._line(self.__off_x_g, i * 200 + 50, self.__off_x_g , 40, "black", 3)
        
        for j in range(0, int(self.__chain_results.hyperperiod + self.__longest_period * self.__period_scale) - 1, 5):
            # Hyperperiod:
            if j > 0 and j % self.__chain_results.hyperperiod == 0:
                self.__img._line(self.__off_x_g + j * self.__scale, i * 200 + 70, self.__off_x_g + j * self.__scale, 40, "black", 3)
                self.__img._text_ellipse("HP", self.__off_x_g + j * self.__scale, i * 200 + 75, "fill: white; stroke: black; stroke-width: 2;")

            elif j  % 10 == 0:
                self.__img._line(self.__off_x_g + j * self.__scale, i * 200 + 50, self.__off_x_g + j * self.__scale, i * 200 + 60)
                self.__img._text(str(j), self.__off_x_g + j * self.__scale, i * 200 + 75)
            else:
               self.__img._line(self.__off_x_g + j * self.__scale, i * 200 + 50, self.__off_x_g + j * self.__scale, i * 200 + 55)
        
        # Draw Arrow on X Axis
        p0x = (self.__chain_results.hyperperiod + self.__longest_period * self.__period_scale) * self.__scale
        p0y = i * 200 + 50
        points_str = "%d,%d %d,%d %d,%d" % (p0x, p0y - 8, p0x, p0y + 8, p0x + 20, p0y)
        self.__img._rectangle(p0x, 0, 50, p0y, "fill:white;")
        self.__img._text("t",p0x, p0y + 25, "")
        self.__img._polygon(points_str, "")
        
    def _get_element(self, _id):
        for e in self.__img.root.getchildren():
            if "id" in e.attrib and e.attrib["id"] == _id:
                return e
        return None

    def draw_robustness_margins(self, options = "first"):
        if options == "all":
            for task in self.__chain_results.job_matrix:
                for job in task:
                    if job.robustness_margin != None :
                        self.__draw_robustness_margins_job(job)

        elif options == "first":
            for task in range(len(self.__chain_results.job_matrix)-1):
                rm = float('inf')
                for job in self.__chain_results.job_matrix[task]:
                    if job.robustness_margin != None:
                        if job.robustness_margin < rm:
                            rm = job.robustness_margin
                            j = job
                self.__draw_robustness_margins_job(j)

        elif options == "last":
            for task in range(len(self.__chain_results.job_matrix)-1):
                rm = float('inf')
                for job in self.__chain_results.job_matrix[task]:
                    if job.robustness_margin != None:
                        if job.robustness_margin <= rm:
                            rm = job.robustness_margin
                            j = job
                self.__draw_robustness_margins_job(j)
        elif options == "none":
            return
        else:
            print(self.CRED+"PYCPA_DRAW -> draw_robustness_margins() Error: Option:\" " + str(options) + "\" is invalid! - Valid Options: all|first|last|none"+self.CEND)

    def __draw_robustness_margins_job(self, job):
        task_num = None
        for i in range(len(self.__chain_results.job_matrix)):
            for j in self.__chain_results.job_matrix[i]:
                if j.name == job.name :
                    task_num = i
        if task_num == None:
            return
        
        off_y = 50 + task_num * 200
        off_x = self.__off_x_g + job.Dmax * self.__scale

        if job.robustness_margin == 0:
            self.__img._line(off_x, off_y + 30 + (job.job_number % 2) * 30, off_x + job.robustness_margin * self.__scale, off_y + 200, "red")
            self.__img._text_ellipse("RM: 0", off_x, off_y + 135, "fill: white; stroke: red; stroke-width: 2;", text_color="red")
        else:
            
            modulus_R = (job.rm_job.Rmax - job.rm_job.Rmin) / job.period + 1
            height_R = 30 / modulus_R
            modulus_D = (job.Dmax - job.Dmin) / job.period + 1
            height_D = 50 / modulus_D

            self.__img._polygon("%d,%d %d,%d %d,%d %d,%d %d,%d %d,%d" % (
                off_x,                                                  off_y + 45  + ((job.job_number - 1) % modulus_D) * height_D,
                off_x,                                                  off_y + 200 + (job.rm_job.job_number % modulus_R) * height_R - (job.robustness_margin * self.__scale / 4),
                off_x + (job.robustness_margin * self.__scale / 4),     off_y + 200 + (job.rm_job.job_number % modulus_R) * height_R,
                off_x + job.robustness_margin * self.__scale,           off_y + 200 + (job.rm_job.job_number % modulus_R) * height_R,
                off_x + job.robustness_margin * self.__scale,           off_y + 45  + ((job.job_number - 1) % modulus_D) * height_D + (job.robustness_margin * self.__scale / 4),
                off_x + job.robustness_margin * self.__scale * 3 / 4,   off_y + 45  + ((job.job_number - 1) % modulus_D) * height_D,
            ), "fill: #F78181; opacity:1;", name="robustness_margin")
            self.__img._text("RM: %d" % job.robustness_margin, off_x + (job.robustness_margin * self.__scale / 2), off_y + 140, "fill: red;")

    def draw_dependency_polygon(self, options = False):
        if options == False:
            return
        
        _len = len(self.__chain_results.path_matrix[0])
        job_min = [None]*_len
        job_max = [None]*_len
        _min = [float('inf')]*_len
        _max = [0]*_len
        
        for i in range(_len):
            for path in self.__chain_results.path_matrix:
                if path[i].job_number <= _min[i]:
                    _min[i] = path[i].job_number
                    job_min[i] = path[i]
                
                if path[i].job_number >= _max[i]:
                    _max[i] = path[i].job_number
                    job_max[i] = path[i]
        
        str_points = ""
        points = list()
        
        off_y = 50
        i = 0

        #modulus_R = (job_min[0].rm_job.Rmax - job_min[0].rm_job.Rmin) / job_min[0].period + 1
        #height_R = 30 / modulus_R
        modulus_D = (job_min[0].Dmax - job_min[0].Dmin) / job_min[0].period + 1
        height_D = 50 / modulus_D

        points.append((
                self.__off_x_g + job_min[0].Rmin * self.__scale,
                off_y
            ))
        
        # BET/LET
        if job_min[0].wcet != None:
            points.append((
                    points[-1][0] + job_min[0].wcet * self.__scale, #self.__off_x_g + (job_min[j].Rmin + ) * self.__scale,
                    off_y + 45 + ((job_min[0].job_number - 1) % modulus_D) * height_D
                ))
        elif job_min[0].let != None:
            points.append((
                    points[-1][0] + job_min[0].let * self.__scale, #self.__off_x_g + (job_min[j].Rmin + ) * self.__scale,
                    off_y + 45 + ((job_min[0].job_number - 1) % modulus_D) * height_D
                ))    
        elif job_min[0].bcrt != None:      
            points.append((
                    points[-1][0] + job_min[0].bcrt * self.__scale, #self.__off_x_g + (job_min[j].Rmin + ) * self.__scale,
                    off_y + 45 + ((job_min[0].job_number - 1) % modulus_D) * height_D
                ))         
        else:
            assert False         
            
        off_y += 200

        for j in range(1,_len):
            
            modulus_R = (job_min[j].Rmax - job_min[j].Rmin) / job_min[j].period + 1
            height_R = 30 / modulus_R
            
            points.append((
                max(points[-1][0], self.__off_x_g + job_min[j].Rmin * self.__scale),
                #points[-1][0] + job_min[j].period * (job_min[j].job_number - 1) * self.__scale,
                off_y + ((job_min[j].job_number - 1) % modulus_R) * height_R
            ))
            points[-2] = points[-1][0], points[-2][1]
            
            modulus_D = (job_min[j].Dmax - job_min[j].Dmin) / job_min[j].period + 1
            height_D = 50 / modulus_D

            if job_min[0].wcet != None:
                points.append((
                    points[-1][0] + job_min[j].wcet * self.__scale, #self.__off_x_g + (job_min[j].Rmin + ) * self.__scale,
                    off_y + 45 + ((job_min[j].job_number - 1) % modulus_D) * height_D
                ))
            elif job_min[0].let != None:
                points.append((
                    points[-1][0] + job_min[j].let * self.__scale, #self.__off_x_g + (job_min[j].Rmin + ) * self.__scale,
                    off_y + 45 + ((job_min[j].job_number - 1) % modulus_D) * height_D
                ))                
            elif job_min[0].bcrt != None:    
                points.append((
                    points[-1][0] + job_min[j].bcrt * self.__scale, #self.__off_x_g + (job_min[j].Rmin + ) * self.__scale,
                    off_y + 45 + ((job_min[j].job_number - 1) % modulus_D) * height_D
                ))               
            else:
                assert False                              
            off_y += 200

        points.append((
            points[-1][0],
            off_y
        ))
        points.append((
            self.__off_x_g + job_max[-1].Dmax * self.__scale,
            off_y
        ))

        for j in reversed(range(_len)):
            off_y -= 200

            modulus_D = (job_max[j].Dmax - job_max[j].Dmin) / job_max[j].period + 1
            height_D = 50 / modulus_D

            if points[-1][0] < self.__off_x_g + job_max[j].Dmax * self.__scale:
                points.append((
                    points[-1][0],
                    off_y + 45 + ((job_max[j].job_number - 1) % modulus_D) * height_D
                ))
            else:
                points.append((
                    self.__off_x_g + job_max[j].Dmax * self.__scale,
                    off_y + 45 + ((job_max[j].job_number - 1) % modulus_D) * height_D
                ))
            
            if points[-2][0] > points[-1][0]:
                points[-2] = (points[-1][0], points[-2][1])
            
            modulus_R = (job_max[j].Rmax - job_max[j].Rmin) / job_max[j].period + 1
            height_R = 30 / modulus_R

            points.append((
                self.__off_x_g + job_max[j].Rmax * self.__scale,
                off_y + ((job_min[j].job_number - 1) % modulus_R) * height_R
            ))
            
        for p in points:
            str_points += "%d, %d " % (p[0], p[1])
    
        self.__img._polygon(str_points, "fill:#F5DA81; stroke:none; opacity:1;", name="dependency_polygon")     

    def draw_max_data_age(self, options = "all"):
        longest_path = None
        max_data_age = 0
        _len = len(self.__chain_results.path_matrix[0])
        if options == "last":
            for path in self.__chain_results.path_matrix:
                if path[-1].Rmax + path[-1].wcrt - path[0].Rmin >= max_data_age :
                    max_data_age = path[-1].Rmax + path[-1].wcrt - path[0].Rmin
                    longest_path = path
            self.__draw_max_data_age_poly(longest_path, max_data_age)

            # Draw Text
            self.__img._text_ellipse("Max Data Age: %d" % max_data_age, self.__off_x_g + (longest_path[0].Rmin + max_data_age / 2) * self.__scale, (_len) * 200, "fill: white; stroke: black; stroke-width: 2;")
            self.__img._line(self.__off_x_g + longest_path[0].Rmin * self.__scale, _len * 200, self.__off_x_g + (longest_path[0].Rmin + max_data_age) * self.__scale, _len * 200)
            self.__img._line(self.__off_x_g + longest_path[0].Rmin * self.__scale, _len * 200 - 20, self.__off_x_g + longest_path[0].Rmin * self.__scale , _len * 200 + 20)
            self.__img._line(self.__off_x_g + (longest_path[0].Rmin + max_data_age) * self.__scale, _len * 200 - 20, self.__off_x_g + (longest_path[0].Rmin + max_data_age) * self.__scale, _len * 200 + 20)
        

        elif options == "first":
            for path in self.__chain_results.path_matrix:
                if path[-1].Rmax + path[-1].wcrt - path[0].Rmin > max_data_age :
                    max_data_age = path[-1].Rmax + path[-1].wcrt - path[0].Rmin
                    longest_path = path
            self.__draw_max_data_age_poly(longest_path, max_data_age)

            # Draw Text
            self.__img._text_ellipse("Max Data Age: %d" % max_data_age, self.__off_x_g + (longest_path[0].Rmin + max_data_age / 2) * self.__scale, (_len) * 200, "fill: white; stroke: black; stroke-width: 2;")
            self.__img._line(self.__off_x_g + longest_path[0].Rmin * self.__scale, _len * 200, self.__off_x_g + (longest_path[0].Rmin + max_data_age) * self.__scale, _len * 200)
            self.__img._line(self.__off_x_g + longest_path[0].Rmin * self.__scale, _len * 200 - 20, self.__off_x_g + longest_path[0].Rmin * self.__scale , _len * 200 + 20)
            self.__img._line(self.__off_x_g + (longest_path[0].Rmin + max_data_age) * self.__scale, _len * 200 - 20, self.__off_x_g + (longest_path[0].Rmin + max_data_age) * self.__scale, _len * 200 + 20)
        
        elif options == "all":
            for path in self.__chain_results.path_matrix:
                if path[-1].Rmax + path[-1].wcrt - path[0].Rmin >= max_data_age :
                    max_data_age = path[-1].Rmax + path[-1].wcrt - path[0].Rmin
                    longest_path = path
            mod = 0
            for path in self.__chain_results.path_matrix:
                if path[-1].Rmax + path[-1].wcrt - path[0].Rmin == max_data_age :
                    self.__draw_max_data_age_poly(path, max_data_age)

                    mod = mod + 1
                    if mod % 2 == 0:
                        self.__img._text_ellipse("Max Data Age: %d" % max_data_age, self.__off_x_g + (path[0].Rmin + max_data_age / 2) * self.__scale, (_len) * 200 - 15, "fill: white; stroke: black; stroke-width: 2;")
                        self.__img._line(self.__off_x_g + path[0].Rmin * self.__scale, _len * 200 - 15, self.__off_x_g + (path[0].Rmin + max_data_age) * self.__scale, _len * 200 - 15)
                        self.__img._line(self.__off_x_g + path[0].Rmin * self.__scale, _len * 200 - 20 - 15, self.__off_x_g + path[0].Rmin * self.__scale , _len * 200 + 20 - 15)
                        self.__img._line(self.__off_x_g + (path[0].Rmin + max_data_age) * self.__scale, _len * 200 - 20 - 15, self.__off_x_g + (path[0].Rmin + max_data_age) * self.__scale, _len * 200 + 20 - 15)
        
                    else:
                        self.__img._text_ellipse("Max Data Age: %d" % max_data_age, self.__off_x_g + (path[0].Rmin + max_data_age / 2) * self.__scale, (_len) * 200 + 15, "fill: white; stroke: black; stroke-width: 2;")
                        self.__img._line(self.__off_x_g + path[0].Rmin * self.__scale, _len * 200 + 15, self.__off_x_g + (path[0].Rmin + max_data_age) * self.__scale, _len * 200 + 15)
                        self.__img._line(self.__off_x_g + path[0].Rmin * self.__scale, _len * 200 - 20 + 15, self.__off_x_g + path[0].Rmin * self.__scale , _len * 200 + 20 + 15)
                        self.__img._line(self.__off_x_g + (path[0].Rmin + max_data_age) * self.__scale, _len * 200 - 20 + 15, self.__off_x_g + (path[0].Rmin + max_data_age) * self.__scale, _len * 200 + 20 + 15)
        elif options == "none":
            return
        else:
            print(self.CRED+"PYCPA_DRAW -> draw_max_data_age() Error: Option:\" " + str(options) + "\" is invalid! - Valid Options: all|first|last|none"+self.CEND)


    
    def __draw_max_data_age_poly(self, path, max_data_age):
           
        _len = len(self.__chain_results.path_matrix[0])

        str_points = ""

        points = list()
        off_y = 50
        points.append((
                self.__off_x_g + path[0].Rmin * self.__scale,
                off_y
            ))
        off_y += _len * 200
        points.append((
                self.__off_x_g + path[0].Rmin * self.__scale,
                off_y
            ))
        points.append((
                self.__off_x_g + (path[0].Rmin + max_data_age) * self.__scale,
                off_y
            ))

        for j in reversed(range(_len)):
            off_y -= 200

            modulus_D = (path[j].Dmax - path[j].Dmin) / path[j].period + 1
            height_D = 50 / modulus_D

            if points[-1][0] < self.__off_x_g + path[j].Dmax * self.__scale:
                points.append((
                    points[-1][0],
                    off_y + 45 + ((path[j].job_number - 1) % modulus_D) * height_D
                ))
            else:
                points.append((
                    self.__off_x_g + path[j].Dmax * self.__scale,
                    off_y + 45 + ((path[j].job_number - 1) % modulus_D) * height_D
                ))
            
            if points[-2][0] > points[-1][0]:
                points[-2] = (points[-1][0], points[-2][1])
            
            modulus_R = (path[j].Rmax - path[j].Rmin) / path[j].period + 1
            height_R = 30 / modulus_R

            points.append((
                self.__off_x_g + path[j].Rmin * self.__scale,
                off_y + ((path[j].job_number - 1) % modulus_R) * height_R
            ))

        for p in points:
            str_points += "%d, %d " % (p[0], p[1])

        self.__img._polygon(str_points, 'fill:black; stroke:none; opacity:0.3;', name="max_data_age")    
        
class draw_dependency_graph(object):
    """Draw Dependency Graph
    """
    __off_x = 20
    __off_y = 40
    __scale = 10
    
    def __init__(self, chain_results):
        self.__chain_results = chain_results
        width, height = self.__calc_img_size()
        self.__img = image("test", width, height)
        self.__draw_hyperPeriod()
        self.__draw_paths()

    def save_file(self, filename=""):
        for c in self.__img.root.getchildren():
            if c.tag == "line":
                self.__img.root.remove(c)
                self.__img.root.insert(0,c)
        
        tree = xml.ElementTree(self.__img.root)
        
        if len(filename) > 4:
            if filename[-4:] == ".svg":
                tree.write(filename)
            else:
                tree.write(filename + ".svg")
        else:
            tree.write(filename + ".svg")

    def __calc_img_size(self):
        x = 0
        y = 0
        for path in self.__chain_results.path_matrix:
            y = 0
            for job in path:
                y += 1
                if job.job_number * job.period > x:
                    x = job.job_number * job.period
        return self.__off_x + x * self.__scale, self.__off_y + y * 100

    def __draw_hyperPeriod(self):
        self.__img._line(
            self.__off_x + self.__chain_results.hyperperiod * self.__scale,
            self.__off_y / 4,
            self.__off_x + self.__chain_results.hyperperiod * self.__scale,
            (len(self.__chain_results.path_matrix[0]) - 0.5) * 100,
            "black"
        )
        self.__img._text(
            "HP",
            self.__off_x + self.__chain_results.hyperperiod * self.__scale,
            (len(self.__chain_results.path_matrix[0])-0.4) * 100
        )
    
    def __draw_paths(self):
        for path in self.__chain_results.path_matrix:
            self.__draw_path(path)

    def __draw_path(self, path):
        colors = ["red", "green", "orange", "blue", "black"]
        for i in range(len(path)-1):
            num, index = self.__times_job_exists(path ,path[i], path[i + 1])
            x1 =    self.__off_x + ((path[i].job_number - 1) * path[i].period + path[i].period * 0.5) * self.__scale
            y1 =    self.__off_y + i * 100
            x2 =    self.__off_x + ((path[i+1].job_number - 1) * path[i+1].period + path[i+1].period * 0.5) * self.__scale
            y2 =    self.__off_y + (i + 1) * 100
            
            off = (index - num / 2) * 5 * math.sqrt(1 + math.pow((x2-x1)/100 ,2)) + 5 / 2
            x1 += off
            x2 += off

            self.__img._line(
                x1,
                y1,
                x2,
                y2,
                colors[(path[0].job_number - 1) % len(colors)],
                4
            )
        i = 0
        for job in path:
            if self.__img._get_element(job.name) == None:
                self.__img._text_circle(job.job_number, self.__off_x + ((job.job_number - 1) * job.period + job.period * 0.5) * self.__scale, self.__off_y + i * 100, job.name)
            i += 1

    def __times_job_exists(self, path, job0, job1):
        n = 0
        c = 0
        i = 0
        pm = self.__chain_results.path_matrix
        for p in range(len(pm)):
               
            for j in range(len(pm[p]) - 1):
                if job0.name == pm[p][j].name and pm[p][j+1].name == job1.name:
                    n += 1
                    if path == pm[p]:
                        i = c
                    else:
                        c += 1 
        return n, i
        
class draw_results(object):

    def __init__(self, chains, tasks):
        self.chains = chains
        self.tasks = tasks
        width, height = self.pixel_size()
        self.__img = image("test.svg", width, height)
        self.color_tasks =  ["#f18d8d","#8df1aa","#f1d08d","#f18de6","#f7f687","#8e8df1","#8df0f1"]
        self.color_chains = ["#df1b1b","#1bdf54","#df9e1b","#df1bc9","#eae910","#1d1bdf","#1cdfe0"]
        self.draw_tasks()

        r = 0
        for chain in chains:            
            self.draw_chain(chain, self.color_chains[r])
            r = (r + 1) % len(self.color_chains)
        self.draw_text_summary()

    def save_file(self, filename=""):
       
        tree = xml.ElementTree(self.__img.root)
        
        if len(filename) > 4:
            if filename[-4:] == ".svg":
                tree.write(filename)
            else:
                tree.write(filename + ".svg")
        else:
            tree.write(filename + ".svg")


    def task_color(self, name):
        r = 0
        for task in self.tasks:
            if task.name == name:
                return self.color_tasks[r]
            r = (r + 1) % len(self.color_tasks)

    def chain_color(self, name):
        r = 0
        for chain in self.chains:
            if chain.name == name:
                return self.color_chains[r]
            r = (r + 1) % len(self.color_chains)

    def draw_chain(self, chain, color):

        for t in range(len(chain.tasks) - 1):

            i1 = self.__img._get_element(chain.tasks[t + 1].name)
            x1 = float(i1.get("x")) + len(str(chain.tasks[t + 1].name)) * 4 + 15
            y1 = float(i1.get("y")) + len(str(chain.tasks[t + 1].name)) * 4 + 15
            
            i2 = self.__img._get_element(chain.tasks[t].name)
            x2 = float(i2.get("x")) + len(str(chain.tasks[t].name)) * 4 + 15
            y2 = float(i2.get("y")) + len(str(chain.tasks[t].name)) * 4 + 15
            
            self.__img._arrow_line(x1, y1, x2, y2, 15, "fill:" + self.chain_color(chain.name))


    def pixel_size(self):
        y = 50
        x = 900
        for c in range(len(self.chains)):
            y += 30 * 4
            for t in range(len(self.chains[c].results.job_matrix) - 1):
                y += 30
        y += 50
        for task in self.tasks:
            y += 30
        y += 50

        return x,y

    def draw_tasks(self):
        ecken = len(self.tasks)
        winkel = math.pi * 2 / ecken
        radius = (ecken * 150) / (2 * math.pi) 
        for t in range(len(self.tasks)):
            x = radius * 1.5 + math.sin(winkel * t) * radius
            y = radius * 1.5 + math.cos(winkel * t) * radius
            self.__img._text_circle(self.tasks[t].name, x, y, self.tasks[t].name, "fill: " + self.task_color(self.tasks[t].name) + "; stroke: black; stroke-width: 3;")
        
    def draw_text_summary(self):
        off_x = (len(self.tasks) * 150) / (math.pi) + 150
        off_y = 50
        if off_x > 600:
            off_y = off_x
            off_x = 50

        for c in range(len(self.chains)):
            off_y += 30
            self.__img._text_line(self.chains[c].name, off_x, off_y, "30px")
            off_y_0 = off_y
            off_y += 30
            self.__img._text_line("  Max Data Age:  " + str(self.chains[c].max_data_age), off_x + 20, off_y, "20px")
            off_y += 30
            self.__img._text_line("  Robustness Margins: ", off_x + 20, off_y, "20px")
            off_y += 30
            for t in range(len(self.chains[c].results.job_matrix) - 1):
                RM = float("inf")
                for j in range(len(self.chains[c].results.job_matrix[t])):
                    if self.chains[c].results.job_matrix[t][j].robustness_margin < RM:
                        RM = self.chains[c].results.job_matrix[t][j].robustness_margin
                task_name = self.chains[c].results.job_matrix[t][j].parent_task.name
                task_name_next = self.chains[c].results.job_matrix[t + 1][j].parent_task.name
                self.__img._text_line(task_name + " to " + task_name_next + ":  " + str(RM), off_x + 30, off_y, "15px")   
                self.__img._circle(off_x + 23, off_y - 5, 5 , "fill:" + self.task_color(task_name))
                off_y += 30             

            self.__img._arrow_line(off_x + 10, off_y - 30, off_x + 10, off_y_0 + 15, 10, "fill:" + self.chain_color(self.chains[c].name))

        off_y += 50
        self.__img._text_line("Robustness Margin (All Chains)", off_x, off_y, "30px")
        for task in self.tasks:
            off_y += 30
            self.__img._text_line(task.name + ":  " + str(task.robustness_margin), off_x + 20, off_y, "20px")
            self.__img._circle(off_x + 8, off_y - 8, 8 , "fill:" + self.task_color(task.name))

class image(object):

    root = None

    def __init__(self, filename, width, height):
        
        self.filename = str(filename)
        self.root = xml.Element("svg", width = str(width), height = str(height))
        
        self.root.set("xmlns", "http://www.w3.org/2000/svg")
        self.root.set("version", "1.1")
        
    def save(self, options = "none"):
        if options ==  "draw_chain":
            for c in self.root.getchildren():
                if c.tag == "line":
                    self.root.remove(c)
                    self.root.insert(0,c)

            for c in self.root.getchildren():
                if c.tag == "polygon":
                    if c.get("name") == "robustness_margin":
                        self.root.remove(c)
                        self.root.insert(0,c)
            for c in self.root.getchildren():
                if c.tag == "polygon":
                    if c.get("name") == "max_data_age":
                        self.root.remove(c)
                        self.root.insert(0,c)
            for c in self.root.getchildren():
                if c.tag == "polygon":
                    if c.get("name") == "dependency_polygon":
                        self.root.remove(c)
                        self.root.insert(0,c)   
        else:
            for c in self.root.getchildren():
                if c.tag == "line":
                    self.root.remove(c)
                    self.root.insert(0,c)
        tree = xml.ElementTree(self.root)
        tree.write(self.filename + ".svg")

    def _get_element(self, _id):
        for e in self.root.getchildren():
            if "id" in e.attrib and e.attrib["id"] == _id:
                return e
        return None

    def _arrow_line(self, x1, y1, x2, y2, width, style):
        _len = math.sqrt((x1 - x2)**2 + (y1 - y2) ** 2)
        n0 =  _len / width
        n = 0
        winkel = math.acos((x1 - x2) / _len)
        if y1 < y2:
            winkel = - winkel
        while(n < n0):
            px = math.cos(winkel) * n * width + x2
            py = math.sin(winkel) * n * width + y2

            p0x = math.cos(winkel) * (n + 1) * width + x2
            p0y = math.sin(winkel) * (n + 1) * width + y2
            dy = math.sin(winkel - math.pi / 2) * width / 2
            dx = math.cos(winkel - math.pi / 2) * width / 2

            self._polygon(
                "%d,%d,%d,%d,%d,%d" % (
                    px + dx ,py + dy,
                    px - dx ,py - dy,
                    p0x, p0y
                ),
                str(style),
                "line_arrow"
            )
            
            n += 1

        for e in self.root.getchildren():
            if e.tag == "polygon":
                    if e.get("name") == "line_arrow":
                        self.root.remove(e)
                        self.root.insert(0,e)


    def _rectangle(self, xx, yy, width, height, style, background = 1):
        e = xml.SubElement(self.root, "rect", x = str(xx), y = str(yy), width = str(width), height = str(height), style = str(style))
        if background == 1:
            self.root.remove(e)
            self.root.insert(0,e)

    def _line(self, x1, y1, x2, y2, color = "black", b = 2):
        xml.SubElement(self.root, "line", x1 = str(x1), y1 = str(y1), x2 = str(x2), y2 = str(y2), style="stroke: " + str(color) + "; stroke-width: " + str(b) + ";" )

    def _text_line(self, text, x, y, font_size):
        sub = xml.SubElement(self.root, "text", x = str(int(x)), y = str(int(y)))
        sub.text = str(text)
        sub.set("font-size", font_size)

    def _text(self, text, xx, yy, style = "", centered = True):
        if centered:
            width = len(text) * 8 + 50
            sub = xml.SubElement(self.root, "svg", x = str(xx - width / 2), y = str(yy-25), style = style)
            sub_t  = xml.SubElement(sub, "text")
            sub_t.set("text-anchor", "middle")
            sub_t.set("style", style)
            xml.SubElement(sub_t, "tspan", x = str(width / 2), y = "30").text = str(text)
        else:
            xml.SubElement(self.root, "text", x = str(int(xx)), y = str(int(yy))).text = str(text)

    def _text_ellipse(self, text, xx , yy, style = "", text_color = "black"):
        width = len(text) * 8 + 50
        sub = xml.SubElement(self.root, "svg", x = str(xx - width / 2), y = str(yy-25), style = style)
        xml.SubElement(sub, "ellipse", cx = str(width / 2), cy = "25", rx = str(width / 2 - 1), ry = "20", style=style )
        sub_t  = xml.SubElement(sub, "text")
        sub_t.set("text-anchor", "middle")
        sub_t.set("style", "stroke-width: 0; fill: " + str(text_color) + ";")
        xml.SubElement(sub_t, "tspan", x = str(width / 2), y = "30").text = str(text)
    
    def _text_circle(self, text, xx, yy, id="", style = "fill: white; stroke: black; stroke-width: 2;"):
        width = len(str(text)) * 8 + 30
        sub = xml.SubElement(self.root, "svg", x = str(xx - width / 2), y = str(yy - width / 2), id = id)
        xml.SubElement(sub, "circle", cx = str(width / 2), cy = str( width / 2), r = str(width / 2 - 1), style=style)
        sub_t  = xml.SubElement(sub, "text")
        sub_t.set("text-anchor", "middle")
        sub_t.set("style", "stroke-width: 0;")
        xml.SubElement(sub_t, "tspan", x = str(width / 2), y = str( width / 2 + 5)).text = str(text)

    def _circle(self, x, y, r, style, id=""):
        xml.SubElement(self.root, "circle", cx = str(x), cy = str(y), r = str(r), style=str(style), id = id)

    def _polygon(self, points, style, name=""):
        xml.SubElement(self.root, "polygon", points = str(points), name = str(name), style = str(style))

    def _rectangle(self, x, y, width, height, style = ""):
        xml.SubElement(self.root, "rect", x = str(x), y = str(y), width = str(width), height = str(height), style = str(style))
