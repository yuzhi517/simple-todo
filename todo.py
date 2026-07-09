#!/usr/bin/env python3
"""
Simple Todo — 一个命令行的待办事项管理工具，它的特点是可以完整支持中文的输入和输出。

使用的方法可以参考下面这几个例子：
    ./todo.py add "买牛奶"
    ./todo.py add "写周报" -p 2
    ./todo.py
    ./todo.py done 1
    ./todo.py search 牛奶

程序会把数据存放在 ~/.simple_todo/tasks.json 这个路径下，用的是单文件的 JSON 格式来保存，不需要再去安装数据库之类的东西。
"""

import json
import os
import sys
import unicodedata
from datetime import datetime

# ── 一些常量定义 ────────────────────────────────────────────────────────

DATA_DIR = os.path.expanduser('~/.simple_todo')
DATA_FILE = os.path.join(DATA_DIR, 'tasks.json')

HELP_TEXT = """\
使用的方法:  todo <命令> [参数...]

可以用的命令:
  add <标题>         往列表里加入一条新的任务
    -p, --priority <数字>   给任务设置一个优先级（如果不写的话默认是 1，数字越小的说明越重要，会排在越前面）

  list               把还没完成的任务都显示出来（不写命令的时候默认就是这个）

  all                显示所有的任务，不管有没有完成都会被列出来

  done <ID>          把指定编号的那条任务改成已完成的状态

  undone <ID>        把已完成的任务重新恢复成未完成

  rm <ID>            从列表里把任务彻底删掉

  search <关键词>    在任务的标题里找包含某个词的任务

  priority <ID> <数字>  修改一条任务的优先级数字

  help               把这段帮助信息显示出来

举几个例子:
  ./todo.py add "完成中期报告" -p 3
  ./todo.py
  ./todo.py done 1
  ./todo.py search 报告
  ./todo.py all
"""


# ── 辅助用的函数 ────────────────────────────────────────────────────────

def ensure_data_dir():
    """检查存放数据的目录是不是已经存在了，如果没有的话就把它创建出来。"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_tasks():
    """从 JSON 文件里面把所有任务的信息读出来，然后返回一个列表。"""
    ensure_data_dir()
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_tasks(tasks):
    """把当前内存里的任务列表写到 JSON 文件里保存好。"""
    ensure_data_dir()
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def display_width(s):
    """
    算一个字符串在终端里显示的时候实际会占多宽的位置。
    像中文这样的字符（CJK 字符）在终端里会占两个列的宽度，而普通的英文字母和数字之类的只占一个列。
    """
    w = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in ('W', 'F'):
            w += 2
        else:
            w += 1
    return w


def pad_to_width(s, target_width):
    """
    往字符串 s 的后面补空格，让它的显示宽度正好等于 target_width 这个值。
    宽度是按照中文占两个列来算的，这样做的目的是为了让表格显示的时候可以对齐。
    """
    current = display_width(s)
    if current >= target_width:
        return s
    return s + ' ' * (target_width - current)


def format_date(ts):
    """把时间戳转换成一个更容易看懂的日期格式的字符串。"""
    if ts is None:
        return ''
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')


def find_task(tasks, task_id):
    """通过任务的编号来找到对应的任务，如果能找到的话就把任务和它所在的位置一起返回，找不到就返回 None 和 -1。"""
    for i, t in enumerate(tasks):
        if t['id'] == task_id:
            return t, i
    return None, -1


def get_next_id(tasks):
    """拿到下一个可以被使用的任务编号。"""
    if not tasks:
        return 1
    return max(t['id'] for t in tasks) + 1


# ── 处理各种命令的函数 ──────────────────────────────────────────────────

def cmd_add(tasks, args):
    """用来往列表里添加一条新任务的函数。"""
    if not args:
        print('出错了: 添加任务的时候需要写上标题才行。')
        return tasks

    title = args[0]
    priority = 1

    # 这里对命令行参数做简单的解析，处理 --priority 和 -p 这两种写法
    i = 1
    while i < len(args):
        if args[i] in ('-p', '--priority') and i + 1 < len(args):
            try:
                priority = int(args[i + 1])
            except ValueError:
                print(f'出错了: 优先级需要是一个整数，而不是 "{args[i + 1]}"')
                return tasks
            i += 2
        else:
            i += 1

    task = {
        'id': get_next_id(tasks),
        'title': title,
        'priority': priority,
        'done': False,
        'created_at': datetime.now().timestamp(),
        'done_at': None,
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f'✓ 已经把任务 [{task["id"]}] 加到列表里了: {title}')
    return tasks


def cmd_list(tasks, show_all=False):
    """把任务显示出来，如果没有特别说明的话就只列还没完成的那些。"""
    visible = tasks if show_all else [t for t in tasks if not t['done']]

    if not visible:
        total = len(tasks)
        if total == 0:
            print('现在还没有任何任务被添加进来。')
        else:
            print('列表里的任务全部都被做完了！🎉')
            print(f'  列表里总共有 {total} 条任务。')
        return

    # 先按照优先级从小到大排列（数字越小越重要），优先级一样的再按照创建时间从早到晚来排
    sorted_tasks = sorted(
        visible,
        key=lambda t: (t['priority'], t['created_at'])
    )

    # 优先级这一列总是显示，算出最宽的宽度
    pri_width = max(max(display_width(f' ★{t["priority"]}') for t in sorted_tasks), 1)

    # 根据任务是否完成来分组显示
    if show_all:
        undone = [t for t in sorted_tasks if not t['done']]
        done = [t for t in sorted_tasks if t['done']]
        groups = [('未完成', undone), ('已完成', done)]
    else:
        groups = [('', sorted_tasks)]

    first_group = True
    for label, group in groups:
        if not group:
            continue

        if label and not first_group:
            print()

        if label:
            header = f'── {label} ──'
            # 下划线稍微宽一点不影响，直接按普通字符来处理就行
            print(header)

        # 算出编号那一列需要的宽度，保证显示的时候可以对齐
        id_width = max(
            max(display_width(str(t['id'])) for t in group),
            2
        )

        for t in group:
            tid_str = pad_to_width(str(t['id']), id_width)
            date_str = f'  [{format_date(t["created_at"])}]'
            pri_str = pad_to_width(f' ★{t["priority"]}', pri_width)
            print(f'  ▸ {tid_str} | {pri_str} | {t["title"]}{date_str}')

        first_group = False


def _get_task_by_id(tasks, args):
    """从参数里把任务编号解析出来，然后去列表里找对应的任务。
    如果在解析的过程中出了问题，会把原因打印出来并返回 None。
    一切顺利的话就返回 (task, index) 这个元组。"""
    if not args:
        print('出错了: 需要指定一个任务的编号。')
        return None
    try:
        task_id = int(args[0])
    except ValueError:
        print(f'出错了: 你给的任务编号 "{args[0]}" 是不对的')
        return None
    task, idx = find_task(tasks, task_id)
    if task is None:
        print(f'出错了: 在列表里没找到编号是 [{task_id}] 的任务')
        return None
    return task, idx


def cmd_done(tasks, args):
    """把一条任务标记成已完成的状态。"""
    result = _get_task_by_id(tasks, args)
    if result is None:
        return tasks
    task, idx = result

    if task['done']:
        print(f'编号为 [{task["id"]}] 的这条任务之前就已经被标记成已完成的状态了。')
        return tasks

    tasks[idx]['done'] = True
    tasks[idx]['done_at'] = datetime.now().timestamp()
    save_tasks(tasks)
    print(f'✓ 任务 [{task["id"]}] 的状态已经改成已完成: {task["title"]}')
    return tasks


def cmd_undone(tasks, args):
    """把任务的已完成标记给去掉，恢复成没完成的状态。"""
    result = _get_task_by_id(tasks, args)
    if result is None:
        return tasks
    task, idx = result

    if not task['done']:
        print(f'编号为 [{task["id"]}] 的这条任务目前就是未完成的状态，不需要再去恢复了。')
        return tasks

    tasks[idx]['done'] = False
    tasks[idx]['done_at'] = None
    save_tasks(tasks)
    print(f'✓ 任务 [{task["id"]}] 的状态已经改回未完成: {task["title"]}')
    return tasks


def cmd_rm(tasks, args):
    """把一条任务从列表里删除掉。"""
    result = _get_task_by_id(tasks, args)
    if result is None:
        return tasks
    task, idx = result

    title = task['title']
    del tasks[idx]
    save_tasks(tasks)
    print(f'✓ 编号为 [{task["id"]}] 的任务已经被删掉了: {title}')
    return tasks


def cmd_search(tasks, args):
    """在任务的标题里面搜索有没有包含某个关键词的任务。"""
    if not args:
        print('出错了: 搜索的时候需要输入一个关键词。')
        return tasks

    keyword = args[0]
    results = [t for t in tasks if keyword.lower() in t['title'].lower()]

    if not results:
        print(f'在标题里没有找到包含 "{keyword}" 的任务。')
        return tasks

    # 搜索结果这里简单打印就行，重新用 cmd_list 的那套逻辑太麻烦了
    print(f'搜索 "{keyword}" 找到了以下结果（一共 {len(results)} 条）:')
    id_width = max(max(display_width(str(t['id'])) for t in results), 2)
    pri_w = max(max(display_width(f' ★{t["priority"]}') for t in results), 1)
    for t in results:
        tid_str = pad_to_width(str(t['id']), id_width)
        pri_str = pad_to_width(f' ★{t["priority"]}', pri_w)
        print(f'  ▸ {tid_str} | {pri_str} | {t["title"]}')


def cmd_priority(tasks, args):
    """修改某一条任务的优先级数字。"""
    if len(args) < 2:
        print('出错了: 需要同时提供任务编号和新的优先级数字。')
        return tasks

    try:
        task_id = int(args[0])
    except ValueError:
        print(f'出错了: 你给的任务编号 "{args[0]}" 是不对的')
        return tasks

    try:
        new_priority = int(args[1])
    except ValueError:
        print(f'出错了: 优先级需要是一个整数，而不是 "{args[1]}"')
        return tasks

    task, idx = find_task(tasks, task_id)
    if task is None:
        print(f'出错了: 在列表里没找到编号是 [{task_id}] 的任务')
        return tasks

    old = tasks[idx]['priority']
    tasks[idx]['priority'] = new_priority
    save_tasks(tasks)
    print(f'✓ 任务 [{task_id}] 的优先级从 {old} 被改成了 {new_priority}: {task["title"]}')
    return tasks


def cmd_menu(tasks):
    """显示一个交互式的菜单界面，用户用数字来选择功能，不需要记命令。"""
    while True:
        # 每次循环先清一下屏幕，保持界面整洁
        os.system('clear' if os.name == 'posix' else 'cls')
        print('=' * 40)
        print('     Simple Todo — 待办事项')
        print('=' * 40)
        print()
        cmd_list(tasks)
        print()
        print('-' * 40)
        print('  1. 添加任务')
        print('  2. 完成任务')
        print('  3. 恢复任务（取消完成）')
        print('  4. 删除任务')
        print('  5. 搜索任务')
        print('  6. 修改优先级')
        print('  7. 查看全部（含已完成）')
        print('  8. 刷新列表')
        print('  0. 退出')
        print('-' * 40)

        choice = input('请选择操作 [0-8]: ').strip()

        if choice == '1':
            title = input('请输入任务标题: ').strip()
            if title:
                pri = input('优先级（1-5，数字越小越重要，默认1，直接回车跳过）: ').strip()
                if pri:
                    cmd_add(tasks, [title, '-p', pri])
                else:
                    cmd_add(tasks, [title])
            else:
                print('标题不能为空，按回车键继续...')
                input()
        elif choice == '2':
            tid = input('请输入要完成的任务编号: ').strip()
            if tid:
                cmd_done(tasks, [tid])
        elif choice == '3':
            cmd_list(tasks, show_all=True)
            print()
            tid = input('请输入要恢复的任务编号: ').strip()
            if tid:
                cmd_undone(tasks, [tid])
        elif choice == '4':
            cmd_list(tasks, show_all=True)
            print()
            tid = input('请输入要删除的任务编号: ').strip()
            if tid:
                cmd_rm(tasks, [tid])
        elif choice == '5':
            keyword = input('请输入搜索关键词: ').strip()
            if keyword:
                cmd_search(tasks, [keyword])
        elif choice == '6':
            cmd_list(tasks, show_all=True)
            print()
            tid = input('请输入任务编号: ').strip()
            pri = input('请输入新的优先级（数字越小越重要）: ').strip()
            if tid and pri:
                cmd_priority(tasks, [tid, pri])
        elif choice == '7':
            cmd_list(tasks, show_all=True)
        elif choice == '8':
            continue
        elif choice == '0':
            print('再见！')
            break
        else:
            print('输入有误，请重新选择')

        if choice != '8':
            print()
            input('按回车键继续...')


# ── 程序的入口 ──────────────────────────────────────────────────────────

def main():
    tasks = load_tasks()
    args = sys.argv[1:]

    if not args:
        cmd_list(tasks)
        return

    command = args[0].lower()

    if command == 'help' or command == '--help' or command == '-h':
        print(HELP_TEXT)
    elif command == 'add':
        cmd_add(tasks, args[1:])
    elif command in ('list', 'ls'):
        cmd_list(tasks)
    elif command == 'all':
        cmd_list(tasks, show_all=True)
    elif command == 'done':
        cmd_done(tasks, args[1:])
    elif command == 'undone':
        cmd_undone(tasks, args[1:])
    elif command in ('rm', 'remove', 'delete'):
        cmd_rm(tasks, args[1:])
    elif command == 'search':
        cmd_search(tasks, args[1:])
    elif command == 'priority':
        cmd_priority(tasks, args[1:])
    elif command == 'menu':
        cmd_menu(tasks)
    else:
        # 也许用户不小心直接输了任务编号或者打错了命令，这里给一个提示
        print(f'不认识这个操作: {command}')


if __name__ == '__main__':
    main()
