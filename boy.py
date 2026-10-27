from math import pi
from pico2d import (
    SDL_KEYDOWN, SDL_KEYUP, SDLK_a, SDLK_LEFT, SDLK_RIGHT, SDLK_SPACE,
    get_time, load_image,
)
from transitions import Machine

class Boy:
    idle_timeout = 5.0
    auto_run_duration = 5.0
    move_speed = 200
    auto_run_speed = 240
    auto_run_size = 120
    auto_run_half_width = auto_run_size // 2
    screen_width = 800
    half_width = 50

    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.pressed_directions = set()
        self.image = load_image('animation_sheet.png')
        self.frame_duration = 0.1
        self.frame_timer = 0
        self.idle_timer = 0
        self.auto_run_timer = 0
        self.last_update_time = get_time()

        self.state_machine = Machine(
            model=self,
            states=['IDLE', 'RUN', 'SLEEP', 'AUTO_RUN'],
            transitions=[
                ['repeat_idle', 'IDLE', 'IDLE'],
                ['start_running', 'IDLE', 'RUN'],
                ['stop_running', 'RUN', 'IDLE'],
                ['go_sleep', 'IDLE', 'SLEEP'],
                ['wake_up', 'SLEEP', 'IDLE'],
                ['start_auto_run', 'IDLE', 'AUTO_RUN'],
                ['finish_auto_run', 'AUTO_RUN', 'IDLE'],
                ['stop_auto_run_for_manual', 'AUTO_RUN', 'RUN'],
            ],
            initial='IDLE',
        )

    def update(self):
        now = get_time()
        elapsed = now - self.last_update_time
        self.last_update_time = now

        if self.state == 'IDLE':
            self.idle_timer += elapsed
            if self.idle_timer >= self.idle_timeout:
                self.go_sleep()
        elif self.state == 'AUTO_RUN':
            self.auto_run_timer += elapsed
            if self.auto_run_timer >= self.auto_run_duration:
                self.finish_auto_run()
                self.idle_timer = 0
                self.frame_timer = 0
            else:
                self.x = max(
                    self.auto_run_half_width,
                    min(self.screen_width - self.auto_run_half_width,
                        self.x + self.face_dir * self.auto_run_speed * elapsed),
                )
                if self.x in (
                    self.auto_run_half_width,
                    self.screen_width - self.auto_run_half_width,
                ):
                    self.face_dir *= -1
        elif self.state == 'RUN':
            self.x = max(
                self.half_width,
                min(self.screen_width - self.half_width,
                    self.x + self.face_dir * self.move_speed * elapsed),
            )

        if self.state in ('IDLE', 'RUN', 'AUTO_RUN'):
            self.frame_timer += elapsed
            while self.frame_timer >= self.frame_duration:
                self.frame_timer -= self.frame_duration
                self.frame = (self.frame + 1) % 8
                if self.state == 'IDLE' and self.frame == 0:
                    self.repeat_idle()

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN and event.key == SDLK_a:
            if self.state == 'IDLE':
                self.start_auto_run()
                self.auto_run_timer = 0
                self.frame_timer = 0
        elif event.type == SDL_KEYDOWN and event.key == SDLK_SPACE:
            if self.state == 'SLEEP':
                self.wake_up()
                self.idle_timer = 0
                self.frame_timer = 0
            elif self.state == 'IDLE':
                self.idle_timer = 0
        elif event.type == SDL_KEYDOWN and event.key in (SDLK_LEFT, SDLK_RIGHT):
            self.pressed_directions.add(event.key)
            self.face_dir = -1 if event.key == SDLK_LEFT else 1
            if self.state == 'SLEEP':
                self.wake_up()
                self.start_running()
                self.frame_timer = 0
            elif self.state == 'IDLE':
                self.start_running()
                self.frame_timer = 0
            elif self.state == 'AUTO_RUN':
                self.stop_auto_run_for_manual()
                self.frame_timer = 0
            if self.state == 'RUN':
                self.idle_timer = 0
        elif event.type == SDL_KEYUP and event.key in (SDLK_LEFT, SDLK_RIGHT):
            self.pressed_directions.discard(event.key)
            if self.state == 'RUN':
                if self.pressed_directions:
                    direction = next(iter(self.pressed_directions))
                    self.face_dir = -1 if direction == SDLK_LEFT else 1
                else:
                    self.stop_running()
                    self.idle_timer = 0
                    self.frame_timer = 0

    def draw(self):
        if self.state == 'SLEEP':
            angle = pi / 2 if self.face_dir == 1 else -pi / 2
            row = 300 if self.face_dir == 1 else 200
            self.image.clip_composite_draw(
                self.frame * 100, row, 100, 100,
                angle, '', self.x, self.y - 30, 100, 100,
            )
            return

        if self.state in ('RUN', 'AUTO_RUN'):
            row = 100 if self.face_dir == 1 else 0
            size = self.auto_run_size if self.state == 'AUTO_RUN' else 100
            self.image.clip_draw(
                self.frame * 100, row, 100, 100,
                self.x, self.y, size, size,
            )
            return

        if self.face_dir == 1:
            self.image.clip_draw(self.frame * 100, 300, 100, 100, self.x, self.y)
        else:
            self.image.clip_draw(self.frame * 100, 200, 100, 100, self.x, self.y)
