import sys
sys.path.insert(0, '/mnt/scratch/third-party-packages/libopencv_3.1.0/lib/python')
sys.path.insert(1, '/mnt/scratch/third-party-packages/libopencv_3.1.0/lib')

import os
import cv2
import fnmatch
import numpy as np

width = 1024
height = 768
frame_diff1 = 1/15.0
fps1 = 15

width_dms = 808
height_dms = 608
frame_diff2 = 1/25.0
fps2 = 25

def read_data(data_path):
    f = open(data_path, 'r')
    human_time = []
    epoch_time = []
    file_name = []
    frame_idx = []
    str = f.readline()
    while (str):
        human_time.append(str[0:27])
        epoch_time.append(str[30:47])
        file_name.append(str[str.find('/mnt'):-1])
        frame_idx.append(int(str[str.find('i') + 1:str.find('cam') - 1]))
        str = f.readline()
    f.close()
    return human_time, epoch_time, file_name, frame_idx

def img2video(file_name, frame_idx, fps, width, height, out_path):
    frame_idx_diff = np.diff(np.array(frame_idx))
    drop_idx = np.argwhere(frame_idx_diff != 1)
    drop_num = (frame_idx_diff - 1)[(frame_idx_diff - 1).nonzero()]

    codec = cv2.VideoWriter_fourcc(*'XVID')
    cap = cv2.VideoWriter(out_path, codec, fps, (width, height))

    k = 0
    count = 0
    file_list = np.chararray(len(frame_idx) + np.sum(drop_num), itemsize=140)
    file_len = len(file_list)
    for i in range(file_len):
        count += 1
        if i in drop_idx:
            for j in range(len(drop_idx)):     # len(drop_idx1) == len(drop_num1)
                file_list[i:i + drop_num[j] + 1] = 'None'
        else:
            file_list[i] = file_name[k]
            k += 1
            if (k == len(file_name)):
                break

    for m in range(file_len):
        print 'frame num = ', m
        if file_list[m] == 'None':
            cap.write(np.zeros((height, width, 3), dtype=np.uint8))
        else:
            cap.write(cv2.imread(file_list[m]))
    print 'done'

    cap.release()
    cv2.destroyAllWindows()
    return file_list, drop_idx, drop_num

def video_align_clip(file_list1, file_list2, file_list):
    start1 = file_list1[0][file_list1[0].find('cam1_') + 5:-4]
    start2 = file_list2[0][file_list2[0].find('cam2_') + 5:-4]
    start = file_list[0][file_list[0].find('cam1_') + 5:-4]
    start_time = np.argmax(np.array([start1, start2, start]))

    end1 = file_list1[-1][file_list1[-1].find('cam1_') + 5:-4]
    end2 = file_list2[-1][file_list2[-1].find('cam2_') + 5:-4]
    end_time = np.argmax(np.array([end1, end2]))

def main():
    demo_path = '/mnt/scratch/sync_sd/car_record/demo/'
    for date_folder in sorted(os.listdir(demo_path)):
        if len(date_folder) == 10 and date_folder != '20160616-1':  # yyyymmdd-X
            print 'date :', date_folder

        test_path = demo_path + date_folder
        out_path_cam1 = '/mnt/scratch/sync_sd/car_record/demo/' + date_folder + '/binocular_camera/' + date_folder + '-cam1-sync.avi'
        out_path_cam2 = '/mnt/scratch/sync_sd/car_record/demo/' + date_folder + '/binocular_camera/' + date_folder + '-cam2-sync.avi'
        out_path_dms = '/mnt/scratch/sync_sd/car_record/demo/' + date_folder + '/binocular_camera/' + date_folder + '-dms-sync.avi'

        # cam1
        human_time1, epoch_time1, file_name1, frame_idx1 = read_data(
            test_path + '/alignment/cam1.txt')
        file_list1, drop_idx1, drop_num1 = img2video(file_name1, frame_idx1, fps1,
                                                     width, height, out_path_cam1)
        # cam2
        human_time2, epoch_time2, file_name2, frame_idx2 = read_data(
            test_path + '/alignment/cam1.txt')
        file_list2, drop_idx2, drop_num2 = img2video(file_name1, frame_idx1, fps1,
                                                     width, height, out_path_cam2)
        # dms
        human_time, epoch_time, file_name, frame_idx = read_data(
            test_path + '/alignment/dms.txt')
        file_list, drop_idx, drop_num = img2video(file_name, frame_idx, fps2,
                                                  width_dms, height_dms, out_path_dms)
    # # videos alignment
    # align_f = open(test_path + 'alignment.txt', 'wa')
    #
    # epoch_time_diff1 = np.diff(np.array(epoch_time1[0:len(epoch_time1)]).astype(np.float))
    # np.argwhere(epoch_time_diff1 > frame_diff1 * 1.5)
    # print epoch_time_diff1 < frame_diff1 / 2
    # flag = epoch_time_diff1 < frame_diff1 / 2
    # for line in flag:
    #     align_f.write("%s\n" % (line))
    #
    #
    # align_f.close()


# if __name__ == '__main__':
#     main()