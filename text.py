import asyncio
import pyautogui

async def item1():
    while True:
        print("1 is running")
        await asyncio.sleep(0)


async def item2():
    # while True:
    #     print("2 is running")
    #     await asyncio.sleep(0)
    await asyncio.gather(item3(), item4())


async def item3():
    while True:
        print("3 is running")
        await asyncio.sleep(1)


async def item4():
    while True:
        print("4 is running")
        await asyncio.sleep(0)


async def main():
    await asyncio.gather(item1(), item2())


if __name__ == '__main__':
    # asyncio.run(main())
    current_screen_size = {'width': 0, 'height': 0}
    my_screen_size = pyautogui.size()
    print(current_screen_size)
