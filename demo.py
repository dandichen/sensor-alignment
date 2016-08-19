import os
import cv2
import glob
import numpy
import ujson
import fnmatch
import linecache
import ConfigParser
from glob import glob
from scipy.spatial import KDTree
from collections import namedtuple


GPS = namedtuple('GPS', ['time', 'altitude', 'anglex', 'angley', 'anglez',
                         'ax', 'ay', 'az', 'gps_height', 'gps_yaw', 'ground_velocity',
                         'hdop', 'hx', 'hy', 'hz', 'latitude', 'longitude',
                         'pdop', 'pressure', 'sn', 'temperature', 'vdop', 'wx', 'wy', 'wz'])
CAN = namedtuple('CAN', ['time', 'attribute', 'value'])

def strCmp(s):
    return float(s[1])

def _get_readable_parse(s):
    if len(s) < 4:
        return None

    frame_id = int(s[2], 16)
    frame_t = float(s[1])
    frame_data = []
    for i in xrange(3, len(s)):
        if s[i] != '':
            frame_data.append(int(s[i], 16))

    if frame_id == 0xc2: # steering  194
        raw = (frame_data[1]<<8) + frame_data[0]
        if frame_data[1] & 0x80:  # 128
            steer = float(raw & 0x7fff) / 0x208a * 360.0 # right
        else:
            steer = -float(raw & 0x7fff) / 0x2024 * 360.0 # left
        return CAN(time=frame_t, attribute='steer', value=steer)

    elif frame_id == 0x380: # acceleration pedal
        raw = frame_data[2]
        acc = float(raw) / 0xfa
        if acc > 1.0:
            acc = 1.0
        return CAN(time=frame_t, attribute='acc', value=acc)

    elif frame_id == 0x1a0: # speed
        raw = (frame_data[3]<<8) + frame_data[2]
        speed = raw / 1860.0 * 10
        return CAN(time=frame_t, attribute='speed', value=speed)

    elif frame_id == 0x390: # steering light
        raw = frame_data[4]
        light_steer = (raw & 0x0f) >> 2
        return CAN(time=frame_t, attribute='light_steer', value=light_steer)

    elif frame_id == 0x4a8: # baking pedal
        raw = ((frame_data[3] << 8) + frame_data[2]) & 0x7ff
        if raw <= 5:
            raw = 0
        brake = float(raw) / 0x64f
        if brake > 1.0:
            brake = 1.0
        return CAN(time=frame_t, attribute='brake', value=brake)

    elif frame_id == 0x440: # throttle
        raw = frame_data[1]
        if raw & 0xf0 == 0x50:
            return CAN(time=frame_t, attribute='throttle', value='D')

        elif raw & 0xf0 == 0x60:
            return CAN(time=frame_t, attribute='throttle', value='N')

        elif raw & 0xf0 == 0x70:
            return CAN(time=frame_t, attribute='throttle', value='R')

        elif raw & 0xf0 == 0x80:
            return CAN(time=frame_t, attribute='throttle', value='P')

        elif raw & 0xf0 == 0xC0:
            return CAN(time=frame_t, attribute='throttle', value='S')

    return None

def readRawData(conf, flag, line_idx):
    if flag == 'cam1' or flag == 'cam2':
        raw_files = conf.get('raw_data', 'binocular_files')
    elif flag == 'dms':
        raw_files = conf.get('raw_data', 'dms_files')
    elif flag == 'gps':
        raw_files = conf.get('raw_data', 'gps_files')
    elif flag == 'can':
        raw_files = conf.get('raw_data', 'can_files')
    else:
        raise ValueError('Wrong file type provided!')

    if line_idx >= 0:  # read specific line
        file_path = linecache.getline(raw_files, line_idx + 1)[:-1]  # start from 1
        file_list = []
        gps_list = []
        steer_list = []
        acc_list = []
        speed_list = []
        light_steer_list = []
        brake_list = []
        throttle_list = []
        for root, _, files in os.walk(file_path):
            for name in files:
                if flag == 'cam1' or flag == 'dms':
                    if fnmatch.fnmatch(name, '*cam1*.jpg'):
                        print file_path.split('/')[6], name
                        file_list.append((root[root.find('demo')+5:root.find('demo')+15] + '_' +
                                          str(int(name[2:name.find('_cam')])) + '_' +
                                          name[name.find('cam'):name.find('cam')+4], float(name[name.find('cam')+5:name.find('.jpg')])))

                elif flag == 'cam2':
                    if fnmatch.fnmatch(name, '*cam2*.jpg'):
                        print file_path.split('/')[6], name
                        file_list.append((root[root.find('demo')+5:root.find('demo')+15] + '_' +
                                          str(int(name[2:name.find('_cam')])) + '_' +
                                          name[name.find('cam'):name.find('cam')+4], float(name[name.find('cam')+5:name.find('.jpg')])))

                elif flag == 'gps':
                    for line in open(os.path.join(root, name), 'r'):
                        try:
                            g = ujson.loads(line.split('\t')[1])
                            if g != {}:
                                print  file_path.split('/')[6], float(line.split('\t')[2])
                                gps_list.append(
                                    GPS(time=float(line.split('\t')[2]),
                                        altitude=g.get('altitude'),
                                        anglex=g.get('anglex'),
                                        angley=g.get('angley'),
                                        anglez=g.get('anglez'),
                                        ax=g.get('ax'),
                                        ay=g.get('ay'),
                                        az=g.get('az'),
                                        gps_height=g.get('gps_height'),
                                        gps_yaw=g.get('gps_yaw'),
                                        ground_velocity=g.get('ground_velocity'),
                                        hdop=g.get('hdop'),
                                        hx=g.get('hx'),
                                        hy=g.get('hy'),
                                        hz=g.get('hz'),
                                        latitude=g.get('latitude'),
                                        longitude=g.get('longitude'),
                                        pdop=g.get('pdop'),
                                        pressure=g.get('pressure'),
                                        sn=g.get('sn'),
                                        temperature=g.get('temperature'),
                                        vdop=g.get('vdop'),
                                        wx=g.get('wx'),
                                        wy=g.get('wy'),
                                        wz=g.get('wz')))
                        except Exception as e:
                            print e.message

                else:
                    for line in open(os.path.join(root, name), 'r'):
                        s = line.split(',')
                        if line.startswith('14'):
                            if len(s) == 3:
                                print file_path.split('/')[6], s[0]
                                if 'steer' in line:
                                    steer_list.append(CAN(time=float(s[0]), attribute=s[1], value=s[2][:-1]))
                                elif 'acc' in line:
                                    acc_list.append(CAN(time=float(s[0]), attribute=s[1], value=s[2][:-1]))
                                elif 'speed' in line:
                                    speed_list.append(CAN(time=float(s[0]), attribute=s[1], value=s[2][:-1]))
                                elif 'light_steer' in line:
                                    light_steer_list.append(CAN(time=float(s[0]), attribute=s[1], value=s[2][:-1]))
                                elif 'brake' in line:
                                    brake_list.append(CAN(time=float(s[0]), attribute=s[1], value=s[2][:-1]))
                                elif 'throttle' in line:
                                    throttle_list.append(CAN(time=float(s[0]), attribute=s[1], value=s[2][:-1]))
                                else:
                                    continue
                            elif len(s) > 3:
                                print file_path.split('/')[6], '.'.join(s[:2])
                                if 'steer' in line:
                                    steer_list.append(CAN(time=float('.'.join(s[:2])), attribute=s[-2], value=s[-1][:-1]))
                                elif 'acc' in line:
                                    acc_list.append(CAN(time=float('.'.join(s[:2])), attribute=s[-2], value=s[-1][:-1]))
                                elif 'speed' in line:
                                    speed_list.append(CAN(time=float('.'.join(s[:2])), attribute=s[-2], value=s[-1][:-1]))
                                elif 'light_steer' in line:
                                    light_steer_list.append(CAN(time=float('.'.join(s[:2])), attribute=s[-2], value=s[-1][:-1]))
                                elif 'brake' in line:
                                    brake_list.append(CAN(time=float('.'.join(s[:2])), attribute=s[-2], value=s[-1][:-1]))
                                elif 'throttle' in line:
                                    throttle_list.append(CAN(time=float('.'.join(s[:2])), attribute=s[-2], value=s[-1][:-1]))
                                else:
                                    continue
                            else:
                                continue
                        elif line.startswith('RAW'):    # 20160626, 20160627, 20160629
                            can = _get_readable_parse(s)
                            if can != None:
                                print file_path.split('/')[6], s[1]
                                if can.attribute == 'steer':
                                    steer_list.append(can)
                                elif can.attribute == 'acc':
                                    acc_list.append(can)
                                elif can.attribute == 'speed':
                                    speed_list.append(can)
                                elif can.attribute == 'light_steer':
                                    light_steer_list.append(can)
                                elif can.attribute == 'brake':
                                    brake_list.append(can)
                                elif can.attribute == 'throttle':
                                    throttle_list.append(can)
                                else:
                                    continue
                        else:
                            continue

        if flag == 'cam1' or flag == 'cam2' or flag == 'dms':
            file_list.sort(key=strCmp)
            return file_list
        elif flag == 'gps':
            return gps_list
        else:
            return steer_list, acc_list, speed_list, light_steer_list, brake_list, throttle_list

def align_can(conf, img_list, can, line_idx, flag):
    fcan = []
    align_result = linecache.getline(conf.get('alignment_result', 'can_result'), line_idx + 1)[:-1]

    _can = [[c.time] for c in can]
    _can = KDTree(_can)
    if flag == 'steer':
        out_f = open(align_result + 'steer_alignment.txt', 'w')
    elif flag == 'acc':
        out_f = open(align_result + 'acc_alignment.txt', 'w')
    elif flag == 'speed':
        out_f = open(align_result + 'speed_alignment.txt', 'w')
    elif flag == 'light_steer':
        out_f = open(align_result + 'light_steer_alignment.txt', 'w')
    elif flag == 'brake':
        out_f = open(align_result + 'brake_alignment.txt', 'w')
    elif flag == 'throttle':
        out_f = open(align_result + 'throttle_alignment.txt', 'w')
    else:
        raise ValueError('Wrong CAN output format!')

    n = 1
    for f in img_list:
        print 'CAN alignment: Processing %d/%d' % (n, len(img_list))
        n += 1
        c = _can.query([f[1]])
        if c[0] > 0.5:
            continue
        c = can[c[1]]
        fcan.append((f[0], c.time, c.attribute, c.value))
        out_f.write('%s %s %s %s\n' % (fcan[-1][0], str(fcan[-1][1]), str(fcan[-1][2]), str(fcan[-1][3])))
    out_f.close()

def align_gps(conf, img_list, gps, line_idx):
    fgps = []
    align_result = linecache.getline(conf.get('alignment_result', 'gps_result'), line_idx + 1)[:-1]

    _gps = [[g.time] for g in gps]
    _gps = KDTree(_gps)
    out_f = open(align_result, 'w')
    n = 1
    for f in img_list:
        print 'GPS alignment: Processing %d/%d' % (n, len(img_list))
        n += 1
        g = _gps.query([f[1]])
        if g[0] > 0.5:
            continue
        g = gps[g[1]]
        fgps.append((f[0], g.time, g.altitude, g.anglex, g.angley, g.anglez, g.ax, g.ay, g.az, g.gps_height, g.gps_yaw,
                     g.ground_velocity, g.hdop, g.hx, g.hy, g.hz, g.latitude, g.longitude, g.pdop, g.pressure, g.sn,
                     g.temperature, g.vdop, g.wx, g.wy, g.wz))
        out_f.write('%s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s\n' %
                    (fgps[-1][0], str(fgps[-1][1]), str(fgps[-1][2]), str(fgps[-1][3]),
                     str(fgps[-1][4]), str(fgps[-1][5]), str(fgps[-1][6]), str(fgps[-1][7]),
                     str(fgps[-1][8]), str(fgps[-1][9]), str(fgps[-1][10]), str(fgps[-1][11]),
                     str(fgps[-1][12]), str(fgps[-1][13]), str(fgps[-1][14]), str(fgps[-1][15]),
                     str(fgps[-1][16]), str(fgps[-1][17]), str(fgps[-1][18]), str(fgps[-1][19]),
                     str(fgps[-1][20]), str(fgps[-1][21]), str(fgps[-1][22]), str(fgps[-1][23])))
    out_f.close()

def preprocess(conf, flag):
    if flag == 'cam1' or flag == 'cam2':
        raw_files = conf.get('raw_data', 'binocular_files')
    elif flag == 'dms':
        raw_files = conf.get('raw_data', 'dms_files')
    elif flag == 'gps':
        raw_files = conf.get('raw_data', 'gps_files')
    elif flag == 'can':
        raw_files = conf.get('raw_data', 'can_files')
    else:
        raise ValueError('Wrong file type provided!')

    lines = open(raw_files).read().splitlines()

    for date in ['20160727', '20160729', '20160801', '20160802']:
        print date
        files = sorted([s for s in lines if date in s])
        if flag == 'cam1' or flag == 'cam2':
            out_files = '/'.join(files[0].split('/')[:8]) + '/alignment/raw_binocular.txt'
        else:
            out_files = '/'.join(files[0].split('/')[:8]) + '/alignment/raw_' + flag + '.txt'
        if len(files) == 1:
            open(out_files, "w").writelines(l for l in open(files[0]).readlines())
        else:
            with open(out_files, 'w') as outfile:
                for fname in files:
                    with open(fname) as infile:
                        for line in infile:
                            outfile.write(line)

def readData(conf, flag, line_idx):
    if flag == 'cam1':
        raw_files = conf.get('raw_data', 'binocular_files')
        file_path = linecache.getline(raw_files, line_idx + 1)[:-1]  # start from 1
        img_list = []
        f = open(file_path)
        lines = f.read().splitlines()
        for line in lines:
            if len(line.split(' ')[1].split('/')) > 5:
                img_list.append((int(line.split(' ')[1].split('/')[-1].split('_')[0][1:]),
                                 float(line.split(' ')[1].split('/')[-1].split('_')[-1][:-5])))
        f.close()
        return img_list

    elif flag == 'gps':
        raw_files = conf.get('raw_data', 'gps_files')
        file_path = linecache.getline(raw_files, line_idx + 1)[:-1]  # start from 1
        gps_list = []
        f = open(file_path)
        lines = f.read().splitlines()
        for line in lines:
            try:
                g = ujson.loads(line.split('\t')[1])
                if g != {}:
                    gps_list.append(
                        GPS(time=float(line.split('\t')[2]),
                            altitude=g.get('altitude'),
                            anglex=g.get('anglex'),
                            angley=g.get('angley'),
                            anglez=g.get('anglez'),
                            ax=g.get('ax'),
                            ay=g.get('ay'),
                            az=g.get('az'),
                            gps_height=g.get('gps_height'),
                            gps_yaw=g.get('gps_yaw'),
                            ground_velocity=g.get('ground_velocity'),
                            hdop=g.get('hdop'),
                            hx=g.get('hx'),
                            hy=g.get('hy'),
                            hz=g.get('hz'),
                            latitude=g.get('latitude'),
                            longitude=g.get('longitude'),
                            pdop=g.get('pdop'),
                            pressure=g.get('pressure'),
                            sn=g.get('sn'),
                            temperature=g.get('temperature'),
                            vdop=g.get('vdop'),
                            wx=g.get('wx'),
                            wy=g.get('wy'),
                            wz=g.get('wz')))
            except Exception as e:
                print e.message
        f.close()
        return gps_list

    elif flag == 'can':
        raw_files = conf.get('raw_data', 'can_files')
        file_path = linecache.getline(raw_files, line_idx + 1)[:-1]  # start from 1
        steer_list = []
        acc_list = []
        speed_list = []
        light_steer_list = []
        brake_list = []
        throttle_list = []
        f = open(file_path)
        lines = f.read().splitlines()
        for line in lines:
            if line.startswith('RAW'):
                s = line.split(',')
                can = _get_readable_parse(s)
                if can != None:
                    if can.attribute == 'steer':
                        steer_list.append(can)
                    elif can.attribute == 'acc':
                        acc_list.append(can)
                    elif can.attribute == 'speed':
                        speed_list.append(can)
                    elif can.attribute == 'light_steer':
                        light_steer_list.append(can)
                    elif can.attribute == 'brake':
                        brake_list.append(can)
                    elif can.attribute == 'throttle':
                        throttle_list.append(can)
                    else:
                        continue

        return steer_list, acc_list, speed_list, light_steer_list, brake_list, throttle_list

    else:
        raise ValueError('Wrong file type provided!')

def main():
    conf = ConfigParser.RawConfigParser()
    params_path = './config/data.cfg'
    if os.path.isfile(params_path):
        conf.read(params_path)
    else:
        raise ValueError('Please provide a correct path for config file')

    for line_idx in range(7):
        cam_list = readData(conf, 'cam1', line_idx)
        # gps_list = readData(conf, 'gps', line_idx)
        # align_gps(conf, cam_list, gps_list, line_idx)

        steer_list, acc_list, speed_list, light_steer_list, brake_list, throttle_list = readData(conf, 'can', line_idx)

        if steer_list != []:
            align_can(conf, cam_list, steer_list, line_idx, 'steer')

        if acc_list != []:
            align_can(conf, cam_list, acc_list, line_idx, 'acc')

        if speed_list != []:
            align_can(conf, cam_list, speed_list, line_idx, 'speed')

        if light_steer_list != []:
            align_can(conf, cam_list, light_steer_list, line_idx, 'light_steer')

        if brake_list != []:
            align_can(conf, cam_list, brake_list, line_idx, 'brake')

        if throttle_list != []:
            align_can(conf, cam_list, throttle_list, line_idx, 'throttle')



if __name__ == '__main__':
    main()
