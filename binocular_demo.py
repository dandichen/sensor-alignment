import os
import numpy as np
from datetime import datetime
import matplotlib.pylab as plt

demo_path = '/mnt/scratch/sync_sd/car_record/demo/'

def main():
    for date_folder in sorted(os.listdir(demo_path)):
        if len(date_folder) == 10:  # yyyymmdd-X
            print 'date :', date_folder
            period_path = demo_path + date_folder + '/binocular_camera/'

            # f1 = open(demo_path + date_folder + '/alignment/cam1.txt', 'wa')
            # f2 = open(demo_path + date_folder + '/alignment/cam2.txt', 'wa')

            for period_folder in sorted(os.listdir(period_path)):
                if os.path.isdir(period_path + period_folder) and (len(period_folder) == 10 or len(period_folder) == 17):
                    # print period_folder
                    folder_path = period_path + period_folder

                    for foldername in sorted(os.listdir(folder_path)):
                        print foldername

                        cam1 = []
                        cam2 = []
                        cam1_file = []
                        cam2_file = []
                        timeline1 = []
                        timeline2 = []

                        file_path = folder_path + str('/') + foldername
                        for file in sorted(os.listdir(file_path)):
                            str1_idx = file.find('cam1_')
                            str2_idx = file.find('cam2_')

                            if str1_idx != -1:
                                cam1.append(file[str1_idx + 5: -4])
                                cam1_file.append(file)
                            if str2_idx != -1:
                                cam2.append(file[str2_idx + 5: -4])
                                cam2_file.append(file)

                        time1 = np.array(cam1).astype(np.float)
                        time2 = np.array(cam2).astype(np.float)

                        len1 = len(cam1)
                        len2 = len(cam2)

                        for i in range(len1):
                            item1 = datetime.utcfromtimestamp(
                                time1[i] + 28800).strftime(
                                "%d %b %Y %H:%M:%S.%f")
                            timeline1.append(item1)
                            # f1.write("%s   %f   %s   %s\n" % (item1, time1[i], cam1_file[i], file_path + '/' + cam1_file[i]))
                            print item1, time1[i], cam1_file[i], file_path + '/' + cam1_file[i]

                        for j in range(len2):
                            item2 = datetime.utcfromtimestamp(
                                time2[j] + 28800).strftime(
                                "%d %b %Y %H:%M:%S.%f")
                            timeline2.append(item2)
                            # f2.write("%s   %f   %s   %s\n" % (item2, time2[j], cam2_file[j], file_path + '/' + cam2_file[j]))
                            print item2, time2[j], cam2_file[j], file_path + '/' + cam2_file[j]

                        # interval1 = np.diff(time1)
                        # interval2 = np.diff(time2)

                        # # visualization
                        # plt.figure()
                        # plt.plot(np.arange(len1 - 1), interval1, 'r',
                        #          label='cam1')
                        # plt.plot(np.arange(len2 - 1), interval2, 'b',
                        #          label='cam2')
                        #
                        # # plt.plot(np.arange(100), interval1[0:100], 'r', label='cam1')
                        # # plt.plot(np.arange(100), interval2[0:100], 'b', label='cam2')
                        # plt.legend()
                        # plt.title('binocular')
                        # plt.waitforbuttonpress()

            # f1.close()
            # f2.close()

# if __name__ == '__main__':
#     main()




