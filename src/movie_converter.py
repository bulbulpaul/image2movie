# coding:utf-8

import sys,os
import glob
import ConfigParser
import logging
import time
import shutil
from argparse import ArgumentParser
from datetime import datetime, timedelta
from collections import OrderedDict

__all__ = []
__version__ = 0.1
__date__ = '2016-06-12'
__updated__ = '2016-12-12'

logging_format = '%(asctime)s- %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=logging_format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def create_args(s_time):
    """
    FFMPEG 実行に関するオプションの作成
    :param s_time: 時間
    """
    ffmpeg_args = OrderedDict([
        ('-y', ''), # 出力先の上書きの許可
        ('-r',str(FRAME_RATE)), # フレームレート 30fps
        ('-i','tmp/%04d.png'),  # ファイル
        ('-an',''), # オーディオ無し
        ('-vcodec','libx264'),  # mp4 フォーマットでエンコーダを H.264
        ('-pix_fmt','yuv420p'), # Quiqtime等互換用に画像形式をYUV420指定
        ('for_upload.mp4',''), # ('value','')
        ('2>>',FFMPEG_LOG.format(s_time.year, s_time.month, s_time.day, s_time.hour))  # ("リダイレクト",ファイル)
        ])
    return ffmpeg_args

def target_file_names(s_time):
    e_time = s_time + timedelta(hours=TIME_LENGTH)
    logger.info('[e_time]' + str(e_time))
    while(s_time < e_time):
        f_name = 'img_{0}{1:0>2}{2:0>2}_{3:0>2}{4:0>2}.png'.format(s_time.year, s_time.month, s_time.day, s_time.hour, s_time.minute)
        if os.path.exists(DATA_DIR):
            os.chdir(DATA_DIR)
            files = glob.glob('*.png')
            if f_name in files:
                yield f_name
            else:
                logger.warn(f_name + ' is not exists')
            s_time += timedelta(minutes=10)

        else:
            raise Exception('directory [{0}] is not exists'.format(f_name))


def copy_targetfiles(s_time):
    """
    convert対象のファイルを一時フォルダへ連番でコピー
    :param s_time: 開始時間  
    """
    # 現時点から-5時間分の画像をテンポラリへ移動
    try:
        # 対象ファイルを連番で保存
        for i, f_name in enumerate(target_file_names(s_time)):
            logger.info('src_file,' + DATA_DIR + f_name)
            logger.info('dest_tmp_file' + TMP_DIR + "{0:0>4}".format(i) + '.png')
            shutil.copyfile(DATA_DIR + f_name, TMP_DIR + "/{0:0>4}".format(i) + '.png')
    except IOError as (errno, strerror):
        logger.warn("I/O error({0}): {1}".format(errno, strerror))

def generate_command(cmd, args):
    """
    shellの実行コマンド文字列の生成
    :param cmd: コマンド
    :param args: オプション引数
    """
    command = cmd
    for opt, value in args.items():
        command += ' ' + opt + ' ' + value
    return command


def __parse_argument():
    """ 
    コマンド引数をパースする 
    """
    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '{name} {version} ({date})'.format(
                                    name=program_name,
                                    version=program_version,
                                    date=program_build_date
                                )

    parser = ArgumentParser()
    parser.add_argument(
        '-V', '--version',
        action='version',
        version=program_version_message
    )
    parser.add_argument(
        '-c', '--config_file',
        dest='config_file',
        help='set config file path',
        required=True
    )

    args = parser.parse_args()
    return args


def __load_config(config_file):
    """ 
    設定ファイルを読み込む
    :param config_file: コンフィグファイル
    """
    config = ConfigParser.ConfigParser()
    config.read(config_file)
    return config


def main():
    # 設定の読み込み
    args = __parse_argument()
    config = __load_config(args.config_file)

    try:
        global DATA_DIR
        DATA_DIR = config.get('storage', 'data_dir')

        storage_type = config.get('storage', 'type')

        global TMP_DIR
        t_dir = config.get('storage', 'tmp_dir')
        if not os.path.exists(DATA_DIR + '/' + t_dir):
            os.mkdir(DATA_DIR + '/' + t_dir)
            TMP_DIR = DATA_DIR + '/'+ t_dir

        global FRAME_RATE
        FRAME_RATE = int(config.get('ffmpeg', 'frame_rate'))

        global TIME_LENGTH
        TIME_LENGTH = int(config.get('ffmpeg', 'time_length'))

        global FFMPEG_LOG
        log_dir = config.get('ffmpeg', 'log_dir')

        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        FFMPEG_LOG = config.get('ffmpeg', 'log_dir') + '/ffmpeg_log_{0}_{1}_{2}_{3}.log'

        base =  datetime.now()
        s = base.replace(minute=0, second=0, microsecond=0) - timedelta(hours=TIME_LENGTH)

        # 対象ファイルの取得
        copy_targetfiles(s)

        # ffmpeg 実行
        ffmpeg_args = create_args(s)
        command = generate_command('ffmpeg',ffmpeg_args)

        os.chdir(DATA_DIR)
        os.system(command)
    except Exception as err:
        logger.exception(err)
        return 1


if __name__ == '__main__':
    main()