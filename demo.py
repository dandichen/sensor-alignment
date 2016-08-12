import os
import cv2
import numpy as np
import linecache
import fnmatch
import ConfigParser
import datetime


def strCmp(s):
    return int(s.split('/')[-1].split('_')[0][1:])

def readRawData(conf, cam_flag, line_idx):
    if cam_flag == 'dms':
        raw_files = conf.get('raw_data', 'dms_files')
    else:
        raw_files = conf.get('raw_data', 'binocular_files')

    file_path = linecache.getline(raw_files, line_idx+1)[0:-1]  # start from 1
    print 'idx = ', line_idx, '', file_path

    cam_list = []
    for dir_name, _, file_list in os.walk(file_path):
        for name in file_list:
            if cam_flag == 'cam2':
                if fnmatch.fnmatch(name, '*cam2*.jpg'):
                    cam_list.append(os.path.join(dir_name, name))
            else:
                if fnmatch.fnmatch(name, '*cam1*.jpg'):
                    cam_list.append(os.path.join(dir_name, name))

    cam_list.sort(key=strCmp)
    return cam_list, file_path

def blackFrame(conf, cam_flag, line_idx, frameIdx):
    head_files = conf.get('raw_data', 'file_lists')
    file_path = linecache.getline(head_files, line_idx)

    if cam_flag == 'dms':
        width = conf.getint('meta_data', 'dms_width')
        height = conf.getint('meta_data', 'dms_height')
        file_name = os.path.join(file_path, 'i' + str(frameIdx).zfill(8) + '_cam1_' + '.'.zfill(11) + '.jpg'.zfill(10))
    else:
        width = conf.getint('meta_data', 'binocular_width')
        height = conf.getint('meta_data', 'binocular_height')
        file_name = os.path.join(file_path, 'i' + str(frameIdx).zfill(8) + '_' + cam_flag + '_' + '.'.zfill(11) + '.jpg'.zfill(10))

    img = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.imwrite(file_name, img)
    return img, file_name

def getFrameLoss(cam_list):
    missing_list = []
    prev = -1
    for path in cam_list:
        num = int(path.split('/')[-1].split('_')[0][1:])
        print num
        if prev != -1 and num - prev != 1:
            missing_list.extend(range(prev + 1, num))
        prev = num
    return missing_list

def getFullFrames(cam_list, cam_flag):
    full_list = []
    prev = -1
    for file_name in cam_list:
        num = int(file_name.split('/')[-1].split('_')[0][1:])
        if prev != -1 and num - prev != 1:
            full_list.extend(['loss'] * (num - prev - 1))
        full_list.append(file_name)
        prev = num
    return full_list

def getTimeList(full_list):
    human_time_list = []
    epoch_time_list = []
    frame_idx = []
    for file_name in full_list:
        if file_name != 'loss':
            frame_idx.append(file_name.split('/')[-1].split('_')[0][1:])
            epoch_time = file_name.split('/')[-1].split('_')[-1][:-4]
            epoch_time_list.append(epoch_time)
            human_time = datetime.datetime.utcfromtimestamp(float(epoch_time) + 28800).strftime("%d %b %Y %H:%M:%S.%f")
            human_time_list.append(human_time)
        else:
            frame_idx.append('loss')
            epoch_time_list.append('loss')
            human_time_list.append('loss')
    return frame_idx, epoch_time_list, human_time_list

def getSyncIdx(conf, cam1_human_time_list, cam2_human_time_list, dms_human_time_list,
               cam1_epoch_time_list, cam2_epoch_time_list, dms_epoch_time_list,
               cam1_frame_idx, cam2_frame_idx, dms_frame_idx):

    i, j, k = 0, 0, 0

    while i < len(cam1_frame_idx) and j < len(cam2_frame_idx) and k < len(dms_frame_idx):
        t1 = cam1_epoch_time_list[i]
        t2 = cam2_epoch_time_list[j]
        t3 = dms_epoch_time_list[k]

        if t1 == 'loss':
            i += 1
            continue
        if t2 == 'loss':
            j += 1
            continue
        if t3 == 'loss':
            k += 1
            continue

        t1, t2, t3 = float(t1), float(t2), float(t3)

        mx = max(t1, t2, t3)
        if mx - t1 >= 0.04:
            i += 1
        if mx - t2 >= 0.04:
            j += 1
        if mx - t3 >= 0.04:
            k += 1
        if mx - t1 < 0.04 and mx - t2 < 0.04 and mx - t3 < 0.04:
            break
    fi, fj, fk = int(cam1_frame_idx[i]), int(cam2_frame_idx[j]), int(dms_frame_idx[k])

    i, j, k = len(cam1_frame_idx)-1, len(cam2_frame_idx)-1, len(dms_frame_idx)-1
    frame_num_cam = 0
    frame_num_dms = 0
    while i >=0 and j >= 0 and k >= 0:
        t1 = cam1_epoch_time_list[i]
        t2 = cam2_epoch_time_list[j]
        t3 = dms_epoch_time_list[k]

        if t1 == 'loss':
            i -= 1
            continue
        if t2 == 'loss':
            j -= 1
            continue
        if t3 == 'loss':
            k -= 1
            continue

        t1, t2, t3 = float(t1), float(t2), float(t3)

        mn = min(t1, t2, t3)
        if t1 == mn:
            fnum = int(cam1_frame_idx[i]) - fi + 1
            if fnum % 75 == 0:
                frame_num_cam = fnum
                frame_num_dms = fnum / 3 * 5
                dms_idx = fk + frame_num_dms - 1 - int(dms_frame_idx[0])
                if frame_num_dms < len(dms_frame_idx) \
                        and dms_frame_idx[dms_idx] != 'loss':
                    break
                else:
                    i -= 1
                    j -= 1
                    k -= 1
                    continue
            else:
                i -= 1
                j -= 1
                k -= 1
                continue
        if t2 == mn:
            fnum = int(cam2_frame_idx[j]) - fj + 1
            if fnum % 75 == 0:
                frame_num_cam = fnum
                frame_num_dms = fnum / 3 * 5
                dms_idx = fk + frame_num_dms - 1 - int(dms_frame_idx[0])
                if frame_num_dms < len(dms_frame_idx) \
                        and dms_frame_idx[dms_idx] != 'loss':
                    break
                else:
                    i -= 1
                    j -= 1
                    k -= 1
                    continue
            else:
                i -= 1
                j -= 1
                k -= 1
                continue
        if t3 == mn:
            fnum = int(dms_frame_idx[k]) - fk + 1
            if fnum % 75 == 0:
                frame_num_dms = fnum
                frame_num_cam = fnum / 5 * 3
                cam_idx = fi + frame_num_cam - 1 - int(cam1_frame_idx[0])
                if frame_num_cam < len(cam1_frame_idx) \
                        and frame_num_cam < len(cam2_frame_idx) \
                        and cam1_frame_idx[cam_idx] != 'loss':
                    break
                else:
                    i -= 1
                    j -= 1
                    k -= 1
                    continue
            else:
                i -= 1
                j -= 1
                k -= 1
                continue
        if frame_num_cam != 0:
            break

    return fi - int(cam1_frame_idx[0]), fi + frame_num_cam - 1 - int(cam1_frame_idx[0]), \
           fj - int(cam2_frame_idx[0]), fj + frame_num_cam - 1 - int(cam2_frame_idx[0]), \
           fk - int(dms_frame_idx[0]), fk + frame_num_dms - 1 - int(dms_frame_idx[0])


    # start_time = max(cam1_human_time_list[0], cam2_human_time_list[0], dms_human_time_list[0])
    # sync_start_datetime = datetime.datetime.strptime(start_time, "%d %b %Y %H:%M:%S.%f") + datetime.timedelta(0, 1) # datetime.datetime
    # sync_start_human_time = sync_start_datetime.strftime("%d %b %Y %H:%M:%S")  # human time
    #
    # end_time = min(cam1_human_time_list[-1], cam2_human_time_list[-1], dms_human_time_list[-1])
    # sync_end_datetime = datetime.datetime.strptime(end_time, "%d %b %Y %H:%M:%S.%f") - datetime.timedelta(0, 2) # datetime.datetime
    #
    # full_sec_dur = int((sync_end_datetime - sync_start_datetime).total_seconds())
    #
    # start_idx1 = [i for i, s in enumerate(cam1_human_time_list) if sync_start_human_time in s][0]
    # start_idx2 = [i for i, s in enumerate(cam2_human_time_list) if sync_start_human_time in s][0]
    # start_idx = [i for i, s in enumerate(dms_human_time_list) if sync_start_human_time in s][0]
    #
    # return start_idx1, start_idx2, start_idx, full_sec_dur

def writeFullFrameLists(full_list, cam_flag, out_path):
    if not os.path.exists(out_path):
        os.mkdir(out_path)

    f = open(out_path + '/' + cam_flag + '-local.txt', 'wa')
    for file_name in full_list:
        if file_name != 'loss':
            frame_idx = file_name.split('/')[-1].split('_')[0][1:]
            epoch_time = file_name.split('/')[-1].split('_')[-1][:-4]
            human_time = datetime.datetime.utcfromtimestamp(float(epoch_time) + 28800).strftime("%d %b %Y %H:%M:%S.%f")
            file_path = '/'.join(file_name.split('/')[-5:])
            f.write("%s %s %s %s\n" % (frame_idx, human_time, epoch_time, file_path))
        else:
            f.write("%s\n" % ('loss'))
    f.close()

def getVideo(conf, full_list, start_idx, end_idx, cam_flag, out_path):
    if not os.path.exists(out_path):
        os.mkdir(out_path)

    if cam_flag == 'dms':
        width = conf.getint('meta_data', 'dms_width')
        height = conf.getint('meta_data', 'dms_height')
        fps = conf.getint('meta_data', 'dms_fps')
    else:
        width = conf.getint('meta_data', 'binocular_width')
        height = conf.getint('meta_data', 'binocular_height')
        fps = conf.getint('meta_data', 'binocular_fps')

    codec = cv2.cv.CV_FOURCC(*'XVID')
    cap = cv2.VideoWriter(out_path + '-'.join([out_path.split('/')[-4], cam_flag + '.avi']), codec, fps, (width, height))

    for idx in range(start_idx, end_idx):
        print out_path + '-'.join([out_path.split('/')[-4], cam_flag + '.avi']), 'idx = ', idx
        if full_list[idx] != 'loss':
            img = cv2.imread(full_list[idx])
        else:
            img = np.zeros((height, width, 3), dtype=np.uint8)
        cap.write(img)
    cap.release()

# def getVideo(conf, full_list, start_idx, full_sec_dur, cam_flag, out_path):
#     if not os.path.exists(out_path):
#         os.mkdir(out_path)
#
#     if cam_flag == 'dms':
#         width = conf.getint('meta_data', 'dms_width')
#         height = conf.getint('meta_data', 'dms_height')
#         fps = conf.getint('meta_data', 'dms_fps')
#     else:
#         width = conf.getint('meta_data', 'binocular_width')
#         height = conf.getint('meta_data', 'binocular_height')
#         fps = conf.getint('meta_data', 'binocular_fps')
#     duration = full_sec_dur * fps
#
#     codec = cv2.cv.CV_FOURCC(*'XVID')
#     cap = cv2.VideoWriter(out_path + '-'.join([out_path.split('/')[-4], 'sync', cam_flag + '-local.avi']), codec, fps, (width, height))
#
#     for idx in range(start_idx, start_idx + duration):
#         print out_path + '-'.join([out_path.split('/')[-4], 'sync', cam_flag + '-local.avi']), 'idx = ', idx
#         if full_list[idx] != 'loss':
#             img = cv2.imread(full_list[idx])
#         else:
#             img = np.zeros((height, width, 3), dtype=np.uint8)
#         cap.write(img)
#     cap.release()
#
# def getVideoClip(conf, full_list, start_idx, full_sec_dur, clip_sec_dur, cam_flag, out_path):
#     if not os.path.exists(out_path):
#         os.mkdir(out_path)
#
#     if cam_flag == 'dms':
#         width = conf.getint('meta_data', 'dms_width')
#         height = conf.getint('meta_data', 'dms_height')
#         fps = conf.getint('meta_data', 'dms_fps')
#     else:
#         width = conf.getint('meta_data', 'binocular_width')
#         height = conf.getint('meta_data', 'binocular_height')
#         fps = conf.getint('meta_data', 'binocular_fps')
#     duration = clip_sec_dur * fps   # 5 min = 5 * 60 * 15/5 * 60 * 25
#     clip_num = full_sec_dur/clip_sec_dur
#
#     codec = cv2.cv.CV_FOURCC(*'XVID')
#
#     for i in range(clip_num):
#         cap = cv2.VideoWriter(out_path + '-'.join([out_path.split('/')[-4], str(i).zfill(3), 'sync', cam_flag + '-local.avi']), codec, fps, (width, height))
#
#         for idx in range(clip_num + start_idx, clip_num + start_idx + duration):
#             print out_path + '-'.join([out_path.split('/')[-4], str(i).zfill(3), 'sync', cam_flag + '-local.avi']), 'idx = ', idx
#             if full_list[idx] != 'loss':
#                 img = cv2.imread(full_list[idx])
#             else:
#                 img = np.zeros((height, width, 3), dtype=np.uint8)
#             cap.write(img)
#         cap.release()

def getVideoClip(conf, full_list, start_idx, end_idx, clip_sec_dur, cam_flag, out_path):
    if not os.path.exists(out_path):
        os.mkdir(out_path)

    align_path = '/mnt/scratch/time_alignment/'
    if cam_flag == 'dms':
        width = conf.getint('meta_data', 'dms_width')
        height = conf.getint('meta_data', 'dms_height')
        fps = conf.getint('meta_data', 'dms_fps')
    else:
        width = conf.getint('meta_data', 'binocular_width')
        height = conf.getint('meta_data', 'binocular_height')
        fps = conf.getint('meta_data', 'binocular_fps')
    clip_frame_dur = clip_sec_dur * fps

    codec = cv2.cv.CV_FOURCC(*'XVID')

    for i in range(start_idx, end_idx, clip_frame_dur):
        cap = cv2.VideoWriter(align_path + '-'.join([out_path.split('/')[-3], str(i/clip_frame_dur).zfill(3), cam_flag + '.avi']), codec, fps, (width, height))
        for idx in range(i, min(end_idx, i+clip_frame_dur)):
            print align_path + '-'.join([out_path.split('/')[-3], str(i/clip_frame_dur).zfill(3), cam_flag + '.avi']), 'idx = ', idx
            if full_list[idx] != 'loss':
                img = cv2.imread(full_list[idx])
            else:
                img = np.zeros((height, width, 3), dtype=np.uint8)
            cap.write(img)
        cap.release()

def main():
    conf = ConfigParser.RawConfigParser()
    params_path = './config/data.cfg'
    if os.path.isfile(params_path):
        conf.read(params_path)
    else:
        raise ValueError('Please provide a correct path for config file')

    for i in range(1, 2):
        cam1_list, out_path1 = readRawData(conf, 'cam1', i)
        cam1_full_list = getFullFrames(cam1_list, 'cam1')
        cam1_frame_idx, cam1_epoch_time_list, cam1_human_time_list = getTimeList(cam1_full_list)
        # writeFullFrameLists(cam1_full_list, 'cam1', '/'.join(out_path1.split('/')[0:-2]) + '/alignment')

        cam2_list, out_path2 = readRawData(conf, 'cam2', i)
        cam2_full_list = getFullFrames(cam2_list, 'cam2')
        cam2_frame_idx, cam2_epoch_time_list, cam2_human_time_list = getTimeList(cam2_full_list)
        # writeFullFrameLists(cam2_full_list, 'cam2', '/'.join(out_path2.split('/')[0:-2]) + '/alignment')

        cam_list, out_path = readRawData(conf, 'dms', i)
        dms_full_list = getFullFrames(cam_list, 'dms')
        dms_frame_idx, dms_epoch_time_list, dms_human_time_list = getTimeList(dms_full_list)
        # writeFullFrameLists(dms_full_list, 'dms', '/'.join(out_path.split('/')[0:-2]) + '/alignment')

        # start_idx1, start_idx2, start_idx, full_sec_dur = getSyncIdx(conf, cam1_human_time_list, cam2_human_time_list, dms_human_time_list,
        #                                                              cam1_epoch_time_list, cam2_epoch_time_list, dms_epoch_time_list,
        #                                                              cam1_frame_idx, cam2_frame_idx, dms_frame_idx)
        #
        # getVideo(conf, cam1_full_list, start_idx1, full_sec_dur, 'cam1', out_path1 + 'sync/')
        # getVideo(conf, cam2_full_list, start_idx2, full_sec_dur, 'cam2', out_path2 + 'sync/')
        # getVideo(conf, dms_full_list, start_idx, full_sec_dur, 'dms', out_path + 'sync/')
        #
        # getVideoClip(conf, cam1_full_list, start_idx1, full_sec_dur, 60 * 5, 'cam1', out_path1 + 'sync/')
        # getVideoClip(conf, cam2_full_list, start_idx2, full_sec_dur, 60 * 5, 'cam2', out_path2 + 'sync/')
        # getVideoClip(conf, dms_full_list, start_idx, full_sec_dur, 60 * 5, 'dms', out_path + 'sync/')

        start_idx1, end_idx1, start_idx2, end_idx2, start_idx, end_idx = getSyncIdx(conf, cam1_human_time_list, cam2_human_time_list, dms_human_time_list,
                                                                                    cam1_epoch_time_list, cam2_epoch_time_list, dms_epoch_time_list,
                                                                                    cam1_frame_idx, cam2_frame_idx, dms_frame_idx)

        # getVideo(conf, cam1_full_list, start_idx1, end_idx1, 'cam1', out_path1 + 'sync/')
        # getVideo(conf, cam2_full_list, start_idx2, end_idx2, 'cam2', out_path2 + 'sync/')
        # getVideo(conf, dms_full_list, start_idx, end_idx, 'dms', out_path + 'sync/')

        # getVideoClip(conf, cam1_full_list, start_idx1, end_idx1, 60 * 5, 'cam1', out_path1)
        # getVideoClip(conf, cam2_full_list, start_idx2, end_idx2, 60 * 5, 'cam2', out_path2)
        getVideoClip(conf, dms_full_list, start_idx, end_idx, 60 * 5, 'dms', out_path)

        print 'done'



if __name__ == '__main__':
    main()
