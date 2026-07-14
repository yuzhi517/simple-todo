#!/usr/bin/env python3
"""Simple Todo CLI — API 客户端入口，命令与原版完全兼容。"""

import sys
from client.api import TodoAPI
from client.display import print_task_list, print_search_results
from client.menu import run_menu

HELP_TEXT = """\
使用方法:  todo <命令> [参数...]

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
  ./cli.py add "完成中期报告" -p 3
  ./cli.py
  ./cli.py done 1
  ./cli.py search 报告
  ./cli.py all
"""


def main():
    args = sys.argv[1:]

    if not args:
        tasks = TodoAPI.list_tasks()
        if tasks is not None:
            total = TodoAPI.list_tasks(show_all=True)
            print_task_list(tasks, total_count=len(total) if total else None)
        return

    command = args[0].lower()

    if command in ('help', '--help', '-h'):
        print(HELP_TEXT)

    elif command == 'add':
        if len(args) < 2:
            print('出错了: 添加任务的时候需要写上标题才行。')
            return

        title = args[1]
        priority = 1

        # 解析 -p / --priority 参数
        i = 2
        while i < len(args):
            if args[i] in ('-p', '--priority') and i + 1 < len(args):
                try:
                    priority = int(args[i + 1])
                except ValueError:
                    print(f'出错了: 优先级需要是一个整数，而不是 "{args[i + 1]}"')
                    return
                i += 2
            else:
                i += 1

        result = TodoAPI.add_task(title, priority)
        if result:
            print(f'✓ 已经把任务 [{result["id"]}] 加到列表里了: {title}')

    elif command in ('list', 'ls'):
        tasks = TodoAPI.list_tasks()
        if tasks is not None:
            total = TodoAPI.list_tasks(show_all=True)
            print_task_list(tasks, total_count=len(total) if total else None)

    elif command == 'all':
        tasks = TodoAPI.list_tasks(show_all=True)
        if tasks is not None:
            print_task_list(tasks, show_all=True, total_count=len(tasks))
            total = len(tasks)
            if total > 0:
                print(f'  列表里总共有 {total} 条任务。')

    elif command == 'done':
        if len(args) < 2:
            print('出错了: 需要指定一个任务的编号。')
            return
        try:
            task_id = int(args[1])
        except ValueError:
            print(f'出错了: 你给的任务编号 "{args[1]}" 是不对的')
            return

        result = TodoAPI.done_task(task_id)
        if result:
            print(f'✓ 任务 [{result["id"]}] 的状态已经改成已完成: {result["title"]}')

    elif command == 'undone':
        if len(args) < 2:
            print('出错了: 需要指定一个任务的编号。')
            return
        try:
            task_id = int(args[1])
        except ValueError:
            print(f'出错了: 你给的任务编号 "{args[1]}" 是不对的')
            return

        # 先检查当前状态，给出合适提示
        task = TodoAPI.get_task(task_id)
        if task and not task.get('done'):
            print(f'编号为 [{task["id"]}] 的这条任务目前就是未完成的状态，不需要再去恢复了。')
        else:
            result = TodoAPI.undone_task(task_id)
            if result:
                print(f'✓ 任务 [{result["id"]}] 的状态已经改回未完成: {result["title"]}')

    elif command in ('rm', 'remove', 'delete'):
        if len(args) < 2:
            print('出错了: 需要指定一个任务的编号。')
            return
        try:
            task_id = int(args[1])
        except ValueError:
            print(f'出错了: 你给的任务编号 "{args[1]}" 是不对的')
            return

        result = TodoAPI.delete_task(task_id)
        if result:
            print(f'✓ 编号为 [{result["id"]}] 的任务已经被删掉了: {result["title"]}') (fix: 修复 Mac → Windows 跨平台兼容性问题)

    elif command == 'search':
        if len(args) < 2:
            print('出错了: 搜索的时候需要输入一个关键词。')
            return

        keyword = args[1]
        results = TodoAPI.search_tasks(keyword)
        if results is not None:
            print_search_results(results, keyword)

    elif command == 'priority':
        if len(args) < 3:
            print('出错了: 需要同时提供任务编号和新的优先级数字。')
            return

        try:
            task_id = int(args[1])
        except ValueError:
            print(f'出错了: 你给的任务编号 "{args[1]}" 是不对的')
            return

        try:
            new_priority = int(args[2])
        except ValueError:
            print(f'出错了: 优先级需要是一个整数，而不是 "{args[2]}"')
            return

        # 先获取旧值用于提示
        old_task = TodoAPI.get_task(task_id)
        if old_task is None:
            return
        result = TodoAPI.set_priority(task_id, new_priority)
        if result:
            print(f'✓ 任务 [{task_id}] 的优先级从 {old_task["priority"]} 被改成了 {new_priority}: {result["title"]}')

    elif command == 'menu':
        run_menu()

    else:
        print(f'不认识这个操作: {command}')


if __name__ == '__main__':
    main()
