import os
import glob
import numpy as np
from datetime import datetime
import matplotlib.pylab as plt

demo_path = '/mnt/scratch/sync_sd/car_record/demo/'

def timeOrder(file_name):
    return int(file_name[file_name.find('i') + 1:file_name.find('_cam1')])


def main():
    for date_folder in sorted(os.listdir(demo_path)):
        if date_folder == '20160616-1':
        # if len(date_folder) == 10:  # yyyymmdd-X
            print 'date :', date_folder
            period_path = demo_path + date_folder + '/dms/'
            f = open(demo_path + date_folder + '/alignment/dms.txt', 'wa')
            for period_folder in sorted(os.listdir(period_path)):
                if os.path.isdir(period_path + period_folder):
                    # print period_folder
                    folder_path = period_path + period_folder

                    for foldername in sorted(os.listdir(folder_path)):
                        print foldername

                        dms_cam1 = []
                        dms_file = []
                        dms_timeline = []
                        file_path = folder_path + str('/') + foldername

                        for file in sorted(os.listdir(file_path), key=timeOrder):
                            dms_cam1.append(file[file.find('cam1') + 5: -4])
                            dms_file.append(file)

                        dms_time = np.array(dms_cam1).astype(np.float)

                        for i in range(len(dms_cam1)):
                            item = datetime.utcfromtimestamp(dms_time[i] + 28800).strftime("%d %b %Y %H:%M:%S.%f")
                            dms_timeline.append(item)
                            f.write("%s   %f   %s   %s\n" % (item, dms_time[i], np.array(dms_file)[np.array(dms_cam1).argsort()][i], file_path + '/' + dms_file[i]))
                            # print item, dms_time[i], \
                            #     np.array(dms_file)[np.array(dms_cam1).argsort()][i], file_path + '/' + dms_file[i]

                        # dms_interval = np.diff(dms_time)

                        # plt.figure()
                        # # plt.plot(np.arange(len(dms_interval)), dms_interval)
                        # plt.plot(np.arange(80), dms_interval[0:80])
                        # plt.legend()
                        # plt.title('dms')
                        # plt.waitforbuttonpress()

            f.close()


    # for dirName, subdirList, fileList in os.walk(demo_path):
    #     for fname in fileList:
    #         if fnmatch.fnmatch(fname, '*.jpg') and len(fname) != 36:
    #             print('\t%s' % fname)

if __name__ == '__main__':
    main()


