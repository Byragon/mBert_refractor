# 生成变异体
# Environment
# conda activate mBert
# java 11

import multiprocessing
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import os
import threading
import subprocess
import math
import time
import json
import pandas as pd

locka = threading.Lock()
from tool工具类 import email_tool


# def get_src_file_path(project_id, version_id,repository_path=None, version_suffix=None):

#     if repository_path is None:
#         repository_path = "/home/changzexing/d4jclean"

#     if version_suffix is None:
#         version_suffix = "b"

#     # obtain the source code folder
#     project_path = "{}/{}/{}".format(
#         repository_path,
#         project_id,
#         version_id + "b"
#     )
#     d4j_export_command = "cd {} && defects4j export -p dir.src.classes".format(project_path)
#     dir_src_classes = os.popen(d4j_export_command).read()
#     src_file_path = "{}/{}/{}/{}".format(
#         repository_path,
#         project_id,
#         version_id + "b",
#         dir_src_classes,
#     )
#     return src_file_path
#  获取源文件的路径
def get_src_file_path(pid, vid, repository_path=None, version_suffix=None):
    if repository_path is None:
        # repository_path = "/home/changzexing/runmutant/Chart/2b"
        repository_path = "/home/changzexing/d4jclean/" + pid + "/" + vid + "b"
    if version_suffix is None:  # 后缀
        version_suffix = "b"

    # obtain the source code folder
    # project_path = "{}/{}/{}".format(
    #     repository_path,
    #     index,
    #     pid + "-" + vid + "b"
    # )
    # d4j_export_command = "cd {} && defects4j export -p dir.src.classes".format(repository_path)
    # dir_src_classes = os.popen(d4j_export_command).read()

    d4j_export_command = ["defects4j", "export", "-p", "dir.src.classes", "$1>/dev/null", "2>&1"]
    # dir_src_classes = subprocess.check_output(d4j_export_command, cwd=repository_path).decode().strip()
    # 包含
    dir_src_classes = subprocess.check_output(d4j_export_command, cwd=repository_path,
                                              stderr=subprocess.DEVNULL).decode().strip()
    src_file_path = "{}/{}".format(
        repository_path,
        dir_src_classes,
    )
    print(f'源路径为{dir_src_classes}')
    return src_file_path


def get_file_lines(file_path):
    with open(file_path, 'r') as f:
        lines = sum(1 for line in f)
    return lines


# 核心函数：source_file_name：源代码文件的路径。line_to_mutate：要变异的代码行号。mutants_directory：变异体的输出路径。max_num_of_mutants：最大变异体数量。method_name：方法名（指定特定的方法名进行变异）
def mBert4FILE(source_file_name, line_to_mutate, mutants_directory, max_num_of_mutants=None, method_name=None):
    if max_num_of_mutants is None:
        max_num_of_mutants = 100

    Path(mutants_directory).mkdir(parents=True, exist_ok=True)

    if method_name is None:
        mBert_command = [
            "bash", "./mBERT.sh",
            f"-in={source_file_name}",
            f"-out={mutants_directory}",
            f"-N={max_num_of_mutants}",
            f"-l={line_to_mutate}"
        ]
        mutate_flag = subprocess.run(mBert_command,
                                     cwd="/home/changzexing/mbert/mBERT-main",
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
        return mutate_flag.returncode


project_data_path = "/home/changzexing/d4jcover"
project_clean_path = "/home/changzexing/d4jclean"
faulty_file_path = "/home/changzexing/faultyFile"
project_mutant_repository_path = "/home/changzexing/mutantFaultyFile"
# if not os.path.exists(project_mutant_repository_path):
#     os.makedirs(project_mutant_repository_path)
Path(project_mutant_repository_path).mkdir(parents=True, exist_ok=True)
version_suffix = "b"

'''
    传入的是ProjectList，VersionList
'''


def getMutant(projectList, versionList, process_name):
    # print('开始执行', projectList, versionList)
    for project_id in projectList:
        for version_id in versionList:
            time_start = time.time()  # 记录循环开始的时间戳
            # print(threading.current_thread().getName())
            # ensure the project version mutant repository 拼接项目路径
            # 开始拼接项目的输出路径：在 Windows 上它会使用反斜杠（\），而在 UNIX 系统上使用斜杠（/）
            project_version_mutant_repository = f"{project_mutant_repository_path}/{project_id}/{project_id.lower()}_{version_id}_{'buggy' if version_suffix == 'b' else 'fixed'}"
            Path(project_version_mutant_repository).mkdir(parents=True, exist_ok=True)
            try:
                # code_scope = pd.read_csv(
                #     os.path.join(
                #         project_data_path, 
                #         project_id,
                #         "{}_{}_code_entity_scope.csv".format(project_id, version_id + version_suffix)
                #     )
                # )
                # print(f"{faulty_file_path}/{project_id}.json")
                with open(f"{faulty_file_path}/{project_id}.json", "r") as f:
                    # 读取json文件
                    code_scope = json.load(f)[f"{project_id}-{version_id}"]
            except FileNotFoundError:
                continue

            # log init
            try:
                log_file_name = os.path.join(
                    project_version_mutant_repository,
                    f"{project_id}_{version_id}{version_suffix}_mutate_log.txt"
                )
                # log_file_name = f"{project_version_mutant_repository}/{project_id}_{version_id}{version_suffix}_mutate_log.txt"
                locka.acquire()
                fp = open(log_file_name, mode="a+", encoding="UTF-8")
                fp.write("")
                fp.close()
            finally:
                locka.release()
            for i in code_scope:
                # src = code_scope.loc[i,"src"]
                src = i
                source_file_name = f"{project_clean_path}/{project_id}/{version_id}b{src}"
                # line_to_mutate = code_scope.loc[i, "line"] + 1
                lines_num = get_file_lines(source_file_name)  # 获取行号
                # print(source_file_name, lines_num)
                for line_item in range(0, lines_num):
                    line_to_mutate = line_item + 1
                    # project_version_mutant_repository为项目的输出路径，code_scope = json.load(f)[f"{project_id}-{version_id}"] 这个路径将用于存放文件File.java第42行的所有变异体。
                    mutants_directory = f"{project_version_mutant_repository}{src[:-5]}/{line_to_mutate}"
                    # print(mutants_directory)
                    # todo 这里需要看下
                    mutate_flag = mBert4FILE(
                        source_file_name=source_file_name,
                        line_to_mutate=line_to_mutate,
                        mutants_directory=mutants_directory,
                    )
                    try:
                        locka.acquire()
                        fp = open(log_file_name, mode="a+", encoding="UTF-8")
                        fp.write("{} : line {} : {} Use jincheng {}\n".format(src, line_to_mutate,
                                                                              "PASS" if mutate_flag == 0 else "ERROR",
                                                                              process_name))
                        fp.close()
                    finally:
                        locka.release()
                        print("{} : line {} : {} Use jincheng {}".format(src, line_to_mutate,
                                                                         "PASS" if mutate_flag == 0 else "ERROR",
                                                                         process_name))
                    time_end = time.time()
                    try:
                        locka.acquire()
                        fp = open(log_file_name, mode="a+", encoding="UTF-8")
                        fp.write(
                            "Mutate {}-{}-{} Over! Use jincheng{} [time cost:{:.2f}]\n".format(project_id, version_id,
                                                                                               src, process_name,
                                                                                               time_end - time_start))
                        fp.write("-" * 50 + "\n")
                        fp.close()
                    finally:
                        locka.release()
                        print("Mutate {}-{}-{} Over! Use jincheng{} [time cost:{:.2f}]".format(project_id, version_id,
                                                                                               src, process_name,
                                                                                               time_end - time_start))
                        print("-" * 50 + "\n")
    # send_email(receiver='changzexing687@163.com', subject="{}-{} 执行完成 148服务器".format(projectList[0], process_name), mail_msg='内容')


def testThread(a, b):
    print(threading.current_thread().getName(), a)
    print(threading.current_thread().getName(), b)


def startThread():
    projectList = [
        "Closure"
    ]
    versionList0 = []
    versionList1 = []
    versionList2 = []
    # versionList3 = []
    for i in range(1, 24):
        versionList0.append(str(i))
    for i in range(24, 47):
        versionList1.append(str(i))
    for i in range(47, 70):
        if str(i) == 63:
            continue
        versionList2.append(str(i))
    # for i in range(48, 66):
    #     versionList3.append(str(i))
    # versionList0 = [
    #     "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25"
    # ]
    # versionList1 = ["26", "27", "28", "29", "30", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25"]
    # versionList2 = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25"]
    versionList = {}
    versionList['0'] = versionList0
    versionList['1'] = versionList1
    versionList['2'] = versionList2
    # versionList['3'] = versionList3
    threads = [threading.Thread(name='t%d' % (i,), target=getMutant, args=(projectList, versionList[str(i)],)) for i in
               range(3)]
    [t.start() for t in threads]
    # 定义进程池
    # pool = multiprocessing.Pool(processes=3)

    # # 定义进程执行的任务列表
    # task_list = [(projectList, versionList[str(i)]) for i in range(3)]

    # # 将任务列表加入进程池中
    # for task in task_list:
    #     pool.apply_async(getMutant, args=task)

    # print('关闭')
    # # 关闭进程池
    # pool.close()

    # # 等待所有进程执行完毕
    # print('加入')
    # pool.join()
    # print('?????')


'''
    这个函数是用来开启多线程的
'''


def startProcess(projectList, svid, evid):
    num = 4  # 多线程的数量
    len = math.ceil((evid - svid + 1) // num)  # 将版本数量平均分为线程的数量
    versionList0 = []
    versionList1 = []
    versionList2 = []
    versionList3 = []
    versionList4 = []
    versionList5 = []
    No = "0"
    for i in range(svid, svid + len):
        if str(i) == No:
            continue
        versionList0.append(str(i))

    for i in range(svid + len, svid + 2 * len):
        if str(i) == No:
            continue
        versionList1.append(str(i))

    for i in range(svid + 2 * len, svid + 3 * len):
        if str(i) == No:
            continue
        versionList2.append(str(i))

    for i in range(svid + 3 * len, evid + 1):
        if str(i) == No:
            continue
        versionList3.append(str(i))

    # for i in range(svid + 4 * len, svid + 5 * len):
    #     if str(i) == No:
    #         continue
    #     versionList4.append(str(i))

    # for i in range(svid + 5 * len, evid + 1):
    #     if str(i) == No:
    #         continue
    #     versionList5.append(str(i))

    versionList = {}
    versionList['0'] = versionList0
    versionList['1'] = versionList1
    versionList['2'] = versionList2
    versionList['3'] = versionList3
    versionList['4'] = versionList4
    versionList['5'] = versionList5

    # Create a process pool with 6 workers
    with ProcessPoolExecutor(max_workers=num) as pool:
        # Submit the jobs to the pool 提交一个任务给多线程
        futures = [pool.submit(getMutant, projectList, versionList[str(i)], 'process%d' % (i,)) for i in range(num)]

        # Wait for all the jobs to complete
        for future in futures:
            future.result()


if __name__ == '__main__':
    # startProcess(["Gson"], 1, 18)
    # startProcess(["Compress"], 1, 47)
    # startProcess(["Jsoup"], 1, 93)
    # startProcess(["Math"], 1, 106)
    # startProcess(["Time"], 1, 27)
    startProcess(["Chart"], 1, 26)
    # startThread()
    # getMutant(["Chart"], ["1"])

# source_file_name = ""
# mutants_directory = ""
# max_num_of_mutants = ""
# line_to_mutate = ""
# method_name = None
# mBert_command = "bash /home/rs/Work/mBERT/mBERT.sh -in={} -out={} -N={} -l={}".format(
#     source_file_name,
#     mutants_directory,
#     max_num_of_mutants,
#     line_to_mutate
# )
