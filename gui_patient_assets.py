"""Cached patient art and the day-two patient pool."""

from functools import partial
from pathlib import Path

import pygame

from PatientData import create_dooski, create_flersch, create_flump, create_roldi


DAY_TWO_PATIENTS = (
    ("flersch", create_flersch, "TRI-031-FL"),
    ("dooski", create_dooski, "VRD-112-DS"),
    ("flump", create_flump, "VEL-064-FP"),
    ("roldi", create_roldi, "CRG-209-RD"),
)


class PatientAssetMixin:
    def patient_sprite(self, name, size):
        key = (name, tuple(size))
        if key not in self.patient_sprite_cache:
            source = pygame.image.load(str(Path(__file__).parent / 'assets' / 'patients' / f'{name}.png')).convert_alpha()
            self.patient_sprite_cache[key] = pygame.transform.smoothscale(source, size)
        return self.patient_sprite_cache[key]

    def fit_patient_sprite(self, name, bounds):
        source_key = (name, 'source')
        if source_key not in self.patient_sprite_cache:
            self.patient_sprite_cache[source_key] = pygame.image.load(str(Path(__file__).parent / 'assets' / 'patients' / f'{name}.png')).convert_alpha()
        source = self.patient_sprite_cache[source_key]
        scale = min(bounds.width / source.get_width(), bounds.height / source.get_height())
        size = (max(1, round(source.get_width() * scale)), max(1, round(source.get_height() * scale)))
        sprite = self.patient_sprite(name, size)
        rect = sprite.get_rect(midbottom=bounds.midbottom)
        self.screen.blit(sprite, rect)
        return rect

    def draw_waiting_asset(self, name, x, width=90, height=133, bottom=469):
        self.fit_patient_sprite(name, pygame.Rect(x - width // 2, bottom - height, width, height))

    def draw_exam_asset(self, name, bay, center_x, platform, shake_x, shake_y, blinking):
        bounds = pygame.Rect(0, 0, 100, bay.height - 32)
        bounds.midbottom = (center_x + shake_x, platform.centery + shake_y)
        rect = self.fit_patient_sprite(name, bounds)
        return pygame.Rect(rect.x, rect.y, rect.width, max(20, rect.height // 3))

    def later_shift_roster(self):
        """Cycle through all eight patients in four-chair shifts after day one."""
        originals = list(self.day_one_queue)
        newcomers = []
        for index, (name, factory, serial) in enumerate(DAY_TWO_PATIENTS):
            entry = dict(originals[index])
            entry.update(create=factory, asset=name, serial=serial,
                         draw=partial(self.draw_waiting_asset, name, entry['chair_x']),
                         exam=partial(self.draw_exam_asset, name))
            newcomers.append(entry)
        # The first later shift introduces all four; subsequent shifts mix casts.
        if self.day_number == 1:
            return newcomers
        pool = originals + newcomers
        offset = (self.day_number - 1) * 3 % len(pool)
        roster = [dict(pool[(offset + i) % len(pool)]) for i in range(4)]
        for entry, seat in zip(roster, originals):
            entry['chair_x'] = seat['chair_x']
            entry['draw'] = partial(self.draw_waiting_asset, entry['asset'], entry['chair_x'])
        return roster
