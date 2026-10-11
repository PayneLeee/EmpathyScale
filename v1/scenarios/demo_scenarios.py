"""Demo scenario definitions for fake-user driven scenario simulation.

The scenario text is used as private memory for the simulated interviewee.
It is not injected directly into the pipeline summary.
"""

DEMO_SCENARIOS = {
    "dual_arm_assembly_island": {
        "slug": "dual_arm_collaborative_assembly_island",
        "description": """
Human worker and a commercial dual-arm collaborative robot jointly assemble
small electronic modules at an assembly island. The robot handles repetitive
picking and pre-positioning, while the human performs fine alignment and
quality confirmation. Communication uses voice, screen confirmations, and RGB
status lights. The environment includes factory noise, fixed lighting, one
worker paired with one robot, and MES-driven takt time.
""".strip(),
        "fake_user_memory": """
I am a process engineer in manufacturing, evaluating a human-robot collaborative
assembly system on a production line.

At an assembly station, a worker and a commercial dual-arm collaborative robot
jointly complete insertion and fastening of small electronic modules. The robot
is responsible for repetitive picking and pre-positioning, while the worker is
responsible for fine alignment and quality confirmation.

The robot platform is a commercial dual-arm cobot with grippers and torque
sensing. It has a small touchscreen on the body, an RGB status light ring, and
a speaker that gives short voice prompts for the next action.

The environment is an assembly island in a factory workshop. There is noise,
fixed task lighting, one worker paired with one robot, and takt is assigned by
MES.

The collaboration mode is that the worker gives a spoken instruction or presses
the screen to confirm, and then the robot begins its sub-task. If the worker
pauses, the robot slows down and waits with a yellow light. The emergency stop
button is on the worker side.

We want to develop or select a scale to measure the worker's perceived robot
empathy, such as whether the system seems to understand the worker's pace,
whether it gives appropriate feedback under pressure, and whether the
communication feels reassuring. The scale should cover feelings brought by
voice, lights, and screen-based multimodal interaction.
""".strip(),
        "seed_queries": [
            "dual arm collaborative robot assembly empathy worker perception voice light screen",
            "human robot collaborative assembly user perception communication reassurance questionnaire",
            "industrial cobot assembly trust comfort multimodal interaction scale",
        ],
        "opening_user_reply": (
            "我是一名制造企业的工艺工程师，正在评估产线上的人机协作机械臂系统。"
            "在装配工位上，工人与一台双臂协作机器人共同完成小型电子模块的插接与紧固。"
            "机器人负责重复性高的拾取与预定位，工人负责精细对准和质量确认。"
        ),
        "scripted_replies": [
            (
                "机器人平台是商用双臂协作臂，末端有夹爪和力矩传感。机身上有小型触摸屏和一圈 RGB 状态灯，"
                "还会用简短语音提示下一步动作。环境是在车间装配岛，有噪声、固定工位照明，两人一机，节拍由 MES 下发。"
            ),
            (
                "协作方式是工人发出口头指令或按屏确认后，机器人开始子任务。若工人停顿，机器人会降低速度并亮黄灯等待。"
                "我们关心的是它是否理解工人的节奏、是否在压力下给出恰当反馈，以及语音、灯光和屏幕这些通道会不会让人更安心。"
            ),
            (
                "和传统自动化设备相比，这个系统的区别不在于它自己完成所有动作，而在于它要配合人的节奏、等待确认、"
                "并通过语音、灯光和屏幕把状态表达清楚。否则工人会觉得它只是在机械执行任务，而不是在配合自己工作。"
            ),
            (
                "最容易出问题的情况是在车间噪声比较大、工人又赶节拍的时候。比如语音提示没听清、灯光状态不明显、"
                "屏幕确认步骤打断手上的装配动作，这时如果机器人没有及时等待、重复说明或给出更清楚的反馈，就会让人觉得不被理解。"
            ),
        ],
    },
    "musculoskeletal_assembly": {
        "slug": "musculoskeletal_side_by_side_assembly",
        "description": """
Human and a musculoskeletal humanoid-style robot sit side-by-side at a shared
assembly workstation, take tools and parts from the same rack, and coordinate
human-only, robot-only, and shared items. The scene includes shared workspace
contention, possible body contact or collision, explicit speech, and implicit
coordination through observing reaching motions, posture, hesitation, and speed.
""".strip(),
        "fake_user_memory": """
I am evaluating a side-by-side human-robot assembly task. A human operator and a
musculoskeletal humanoid-style robot sit next to each other at the same assembly
workstation. They take parts and tools from a shared tool rack and assemble a
small product together.

Some objects can only be picked by the human because they require delicate
finger handling or judgment. Some objects can only be picked by the robot
because they are heavy or positioned closer to its side. Some objects can be
picked by either partner. This creates a shared-resource problem: sometimes the
human and robot reach toward the same shelf area, and one partner must wait,
yield, or choose a different order.

The robot is not a traditional rigid industrial arm. It has a human-like
musculoskeletal body with compliant joints, visible limbs, and body-like
reaching motions. Because the human and robot sit close together,
there can be accidental body contact, arm crossing, or near-collisions in the
shared workspace. The contact risk feels different from a fenced robot arm
because the robot body is near the human's torso and arms.

They can use simple spoken phrases such as \"I will take this one\", \"please
wait\", \"your turn\", or \"I cannot reach that part\". They also coordinate
implicitly: the human watches the robot's arm trajectory, hesitation, speed,
and posture to infer its intention, and the robot should appear to notice when
the human is reaching, hesitating, or giving way.

The most uncomfortable moments are when both reach for the same tool, when the
robot occupies the same access path and blocks access, when the human cannot tell whether the
robot has noticed their hand, or when a soft body contact happens and the robot
does not acknowledge it. A caring or empathic robot would modulate its approach near the
human, leave space, verbally clarify its intent, wait when the human reaches
first, and show through motion or speech that it is considering the human's
comfort and task needs.

Please use the short scenario name musculoskeletal_side_by_side_assembly if
asked.
""".strip(),
        "seed_queries": [
            "musculoskeletal humanoid robot human robot collaboration shared workspace",
            "side by side human robot assembly implicit coordination action observation",
            "human robot physical interaction collision contact comfort collaborative assembly",
        ],
        "scripted_replies": [
            (
                "主要靠简短语言和动作配合。它会说“我来拿这个”或“你先拿”，同时我会看它手臂是否暂停、让位、"
                "换路径或者先缩回一点来判断它的意图。这里关键不是它动作慢，而是它会不会及时表明意图、避让，"
                "以及在共享工具架前给我留空间。"
            ),
            (
                "它和传统刚性机械臂最不一样的是身体性和共享空间。传统机械臂通常有明确工作边界，人不会和它并排"
                "挤在同一个取物区；这个肌肉骨骼机器人就在我旁边，我们会伸向同一个工具架区域，手臂轨迹和上半身距"
                "离都更像两个人在协作，所以我会更在意它是否在考虑我的空间和舒适感。"
            ),
            (
                "最容易出问题的情况是两个人几乎同时去拿同一层架位上的零件，或者一方以为另一方已经看见自己在伸手。"
                "这时最不舒服的不是速度快慢，而是会不会挡住我、擦碰到我、或者碰到之后没有任何停顿、避让或说明。"
            ),
        ],
        "opening_user_reply": (
            "我们在评估一个并排装配场景：人和肌肉骨骼机器人坐在同一个装配工位旁边，"
            "一起从共享工具架取零件和工具完成装配。人负责更精细、需要判断的拿取，机器人负责更重或更靠近它那一侧的物品；"
            "如果时序或配合出错，就容易出现同时伸手、互相挡住，甚至轻微身体接触或碰撞。"
        ),
    }
}


def get_demo_scenario(name: str) -> dict:
    if name not in DEMO_SCENARIOS:
        available = ", ".join(sorted(DEMO_SCENARIOS))
        raise KeyError(f"Unknown demo scenario '{name}'. Available: {available}")
    return DEMO_SCENARIOS[name]
