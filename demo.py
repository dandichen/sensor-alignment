import os
import cv2
import glob
import numpy
import ujson
import fnmatch
import linecache
import ConfigParser
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
    frame_t = s[1]
    frame_data = []
    for i in xrange(3, len(s)):
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
        for root, _, files in os.walk(file_path):
            for name in files:
                if flag == 'cam1' or flag == 'dms':
                    if fnmatch.fnmatch(name, '*cam1*.jpg'):
                        print name
                        file_list.append((root[root.find('demo')+5:root.find('demo')+15] + '_' +
                                          str(int(name[2:name.find('_cam')])) + '_' +
                                          name[name.find('cam'):name.find('cam')+4], float(name[name.find('cam')+5:name.find('.jpg')])))
                    file_list.sort(key=strCmp)
                elif flag == 'cam2':
                    if fnmatch.fnmatch(name, '*cam2*.jpg'):
                        print name
                        file_list.append((root[root.find('demo')+5:root.find('demo')+15] + '_' +
                                          str(int(name[2:name.find('_cam')])) + '_' +
                                          name[name.find('cam'):name.find('cam')+4], float(name[name.find('cam')+5:name.find('.jpg')])))
                    file_list.sort(key=strCmp)
                elif flag == 'gps':
                    for line in open(os.path.join(root, name), 'r'):
                        try:
                            g = ujson.loads(line.split('\t')[1])
                            if g != {}:
                                print float(line.split('\t')[2])
                                file_list.append(
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
                                file_list.append(CAN(time=float(s[0]),
                                                     attribute=s[1],
                                                     value=s[2][:-1]))
                            elif len(s) > 3:
                                file_list.append(CAN(time=float('.'.join(s[:2])),
                                                     attribute=s[-2],
                                                     value=s[-1][:-1]))
                            else:
                                raise ValueError('Wrong CAN data format!')
                        elif line.startswith('RAW'):    # 20160626, 20160627, 20160629
                            file_list.append(_get_readable_parse(s))
                        else:
                            continue

    return file_list

def align_gps(conf, img_list, gps, line_idx):
    fgps = []
    align_result = linecache.getline(conf.get('alignment_result', 'gps_result'), line_idx + 1)[:-1]

    _gps = [[g.time] for g in gps]
    _gps = KDTree(_gps)
    out_f = open(align_result, 'w')
    n = 1
    for f in img_list:
        print align_result.split('/')[6], 'Processing %d/%d' % (n, len(img_list))
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


def main():
    conf = ConfigParser.RawConfigParser()
    params_path = './config/data.cfg'
    if os.path.isfile(params_path):
        conf.read(params_path)
    else:
        raise ValueError('Please provide a correct path for config file')

    for line_idx in range(2, 9):
        print 'line_idx = ', line_idx
        cam_list = readRawData(conf, 'cam1', line_idx)
        gps_list = readRawData(conf, 'gps', line_idx)
        align_gps(conf, cam_list, gps_list, line_idx)

        # file_path = linecache.getline(raw_files, line_idx + 1)[:-1]
        # for root, _, files in os.walk(file_path):
        #     for name in files:
        #         print os.path.join(root, name)


if __name__ == '__main__':
    main()

# def align_can():
