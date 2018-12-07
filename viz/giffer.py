import os
import sys
from pathlib import Path
dirname = (Path(__file__)).parents[0]
sys.path.append(os.path.join(dirname))
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import imageio
import seaborn as sns
import numpy as np


class GifWrap(object):
    """
    Used to create a gif to show progression of data over time in weekly frames

    Todo:
        * Add the ability to pass the data aggregation for the gif
        * Add the ability to simulate frames between datapoints to make smooth animations

    """
    def __init__(self, x_col=None, y_col=None, size_col=None, time_col=None, group_by=None, data=None):
        self.images = []
        self.imagenum = 1
        self.imgpaths = []
        if data:
            self.data = data
        else:
            self.raw_data = pd.read_csv(os.path.join(dirname, r'fake.csv'))

        self.x = x_col if x_col else 'tat'
        self.y = y_col if y_col else 'rating'
        self.z = size_col if size_col else 'consult_id'
        self.time_col = time_col if time_col else 'submitted_at'
        self.group_by = group_by if group_by else 'role'
        sns.set_style("whitegrid")

    def _slice_frames(self, date_agg=None):
        # Trim cols
        self.data = self.raw_data[[self.x, self.y, self.z, self.time_col, self.group_by]]
        # Convert date col to datetime
        self.data[self.time_col] = pd.to_datetime(self.data[self.time_col], errors='coerce')
        if date_agg == 'weekly':
            # Add col for week number in the year
            self.data['framenum'] = self.data[self.time_col].dt.strftime("%U")
        elif date_agg == 'daily':
            self.data['framenum'] = self.data[self.time_col].dt.strftime("%j")
        elif date_agg == 'monthly':
            self.data['framenum'] = self.data[self.time_col].dt.strftime("%m")

        # Subset data
        self.framenum = int(min(self.data['framenum']))
        self._color_groups()

    def _frame_data(self, framenum=None):
        # Add week number column to data
        frame_data = self.data[self.data['framenum'] == str(self.framenum if not framenum else framenum)]
        # Group data by role and date
        agg_dict = dict(zip([self.x, self.y, self.z], [self.x_agg, self.y_agg, self.z_agg]))
        agg_dict = {k: v for k, v in agg_dict.items() if v is not None}
        ### Some Problem right here
        na_dict = {self.x: 0, self.y: 0, self.z: np.NaN, self.group_by: 'none'}
        frame_data = frame_data.groupby([self.group_by, 'framenum'], as_index=False)
        frame_data = frame_data.agg(agg_dict)
        return frame_data

    def _color_groups(self):
        groups = list(self.data[self.group_by].unique())
        colors = ['maroon', 'blue', 'green', 'purple', 'orange', 'black', 'yellow', 'olive', 'teal']
        colors = colors[0:len(groups)]
        # Assign values to colors
        self.color_dict = dict(zip(groups, colors))
        self.legend_obj = []
        for k, v in self.color_dict.items():
            self.legend_obj.append(mpatches.Circle((0, 0), alpha=.3, color=v))

    def _plot_frame(self):
        self.frame_data = self._frame_data()
        self._setup_frame()
        print(type(self.frame_data[self.z]))
        plt.scatter(self.frame_data[self.x], self.frame_data[self.y], alpha=.3,
                    s=self.frame_data[self.z]*self.frame_data[self.z].quantile(),
                    color=[self.color_dict[i] for i in self.frame_data[self.group_by]])

        plt.legend(self.legend_obj, self.color_dict.keys())
        path = os.path.join(dirname, f'sample/file{self.imagenum}.png')
        plt.savefig(fname=path, quality=95)
        self.images.append(imageio.imread(path))
        self.imgpaths.append(path)
        plt.clf()
        #self._smooth()
        self.imagenum += 1
        self.framenum += 1

    def _setup_frame(self):
        # Set axes limits
        plt.xlim(0, 15)
        plt.ylim(0, 6)
        # Add week number to frame
        plt.figtext(.75, .9, f'{self.framenum}/{max(self.data["framenum"])}')
        plt.xlabel(f'X-axis: {self.x_agg}({self.x})  |  Z-axis: {self.z_agg}({self.z})')
        plt.ylabel(f'Y-axis: {self.y_agg}({self.y})')

    def _smooth(self, frames=1):
        names = ['a', 'b', 'c', 'd', 'e']
        added_frame = 1
        next_frame_data = self._frame_data(framenum=self.framenum + 1)
        groups = list(next_frame_data[self.group_by].unique())
        last_frame_data = self.frame_data[self.frame_data[self.group_by].isin(groups)]
        while added_frame <= frames and self.framenum <= int(max(self.data['framenum'])):
            self._setup_frame()
            x_change = (added_frame/(frames+1))*(next_frame_data[self.x].subtract(last_frame_data[self.x]))
            y_change = (added_frame/(frames+1))*(next_frame_data[self.y].subtract(last_frame_data[self.y]))
            z_change = (added_frame/(frames+1))*(next_frame_data[self.z].subtract(last_frame_data[self.z]))
            #print(x_change)
            #print(self.frame_data)
            #print(self.frame_data[self.x].add(x_change))
            plt.scatter(x=self.frame_data[self.x].add(x_change), y=self.frame_data[self.y].add(y_change), alpha=.3,
                        s=self.frame_data[self.z].add(z_change)*self.frame_data[self.z].quantile(),
                        color=[self.color_dict[i] for i in self.frame_data[self.group_by]])
            plt.legend(self.legend_obj, self.color_dict.keys())
            path = os.path.join(dirname, f'sample/file{self.imagenum}{names[added_frame -1]}.png')
            plt.savefig(fname=path, quality=95)
            self.images.append(imageio.imread(path))
            self.imgpaths.append(path)
            plt.clf()
            added_frame += 1

    def make_gif(self, x_agg=None, y_agg=None, z_agg='count', time_agg='weekly'):
        self._slice_frames(time_agg)
        self.x_agg = x_agg
        self.y_agg = y_agg
        self.z_agg = z_agg

        while self.framenum <= int(max(self.data['framenum'])):
            self._plot_frame()
        plt.close()
        imageio.mimsave(os.path.join(dirname, r'sample/final.gif'), self.images, fps=2)
        for i in self.imgpaths:
            os.remove(i)

