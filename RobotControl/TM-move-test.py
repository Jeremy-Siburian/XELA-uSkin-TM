import asyncio
import techmanpy
import time

async def initial_pos(conn):
    blending_perc = 1.0
    relative_to_tcp = False
    use_precise_positioning = False
    await conn.move_to_joint_angles_ptp([13.511, 2.458, 87.040, 0.831, 88.584, 14.927], 1.0, 200)

async def pick_pos(conn):
    blending_perc = 1.0
    relative_to_tcp = False
    use_precise_positioning = False
    await conn.move_to_joint_angles_ptp([12.633, 30.844, 108.238, -48.883, 88.581, 14.926], 1.0, 200)
    await conn.set_queue_tag(1, wait_for_completion=True)

async def waypoint_1(conn):
    blending_perc = 1.0
    relative_to_tcp = False
    use_precise_positioning = False
    await conn.move_to_joint_angles_ptp([12.969, 14.555, 97.971, -22.319, 88.504, 15.313], 0.50, 200)

async def waypoint_2(conn):
    blending_perc = 1.0
    relative_to_tcp = False
    use_precise_positioning = False
    await conn.move_to_joint_angles_ptp([-19.610, 20.141, 90.185, -21.389, 88.503, 15.283], 0.50, 200)

async def place_pos(conn):
    blending_perc = 1.0
    relative_to_tcp = False
    use_precise_positioning = False
    await conn.move_to_joint_angles_ptp([-19.613, 33.626, 100.164, -44.853, 88.568, 15.232], 0.50, 200)
    await conn.set_queue_tag(2, wait_for_completion=True)

async def waypoint_3(conn):
    blending_perc = 1.0
    relative_to_tcp = False
    use_precise_positioning = False

    await asyncio.sleep(2)
    await conn.move_to_joint_angles_ptp([-19.610, 20.141, 90.185, -21.389, 88.503, 15.283], 0.70, 200)

async def return_to_initial(conn):
    blending_perc = 1.0
    relative_to_tcp = False
    use_precise_positioning = False
    await conn.move_to_joint_angles_ptp([13.511, 2.458, 87.040, 0.831, 88.584, 14.927], 0.70, 200)
    await conn.set_queue_tag(4, wait_for_completion=True)

#Main thread for robot movement

async def main():
    async with techmanpy.connect_sct(robot_ip='192.168.5.20') as conn:
        while True:
            await initial_pos(conn)
            await pick_pos(conn)
            await waypoint_1(conn)
            await waypoint_2(conn)
            await place_pos(conn)
            await waypoint_3(conn)
            await return_to_initial(conn)

asyncio.run(main())