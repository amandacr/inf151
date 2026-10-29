"""Centralized music, sound-effect, and mute controls for The Cosmic Clinic."""

from array import array
import math
from pathlib import Path
import random

import pygame

from gui_theme import COLORS


class AudioMixin:
    """Generate and play the game's small set of retro medical sound effects."""

    def setup_audio(self):
        """Initialize balanced music/effect levels and synthesize reusable sounds."""

        self.audio_available = False
        self.audio_muted = False
        self.music_volume = 0.12
        self.sfx_volume = 0.72
        self.sound_effects = {}
        self.audio_button = pygame.Rect(16, 16, 112, 31)

        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.sound_effects = self.build_sound_effects()
            self.audio_available = True
        except pygame.error:
            # The game remains fully playable on machines without an audio device.
            self.sound_effects = {}

    def start_music(self):
        """Start the quieter background track without blocking a silent fallback."""

        if not self.audio_available:
            return
        music_path = Path(__file__).resolve().parent / "assets" / "hyperdrive_boogie_bg_music.ogg"
        try:
            pygame.mixer.music.load(str(music_path))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(loops=-1)
        except pygame.error:
            return

    def build_sound_effects(self):
        """Create the complete sound set from lightweight synthesized waveforms."""

        click = self.make_tone(
            0.075,
            lambda t, duration: 0.34
            * self.sound_envelope(t, duration, 0.004, 0.05)
            * math.sin(2 * math.pi * (720 - 180 * t / duration) * t),
        )
        card = self.make_tone(
            0.12,
            lambda t, duration: 0.30
            * self.sound_envelope(t, duration, 0.006, 0.07)
            * (
                math.sin(2 * math.pi * 485 * t)
                + 0.35 * math.sin(2 * math.pi * 970 * t)
            ),
        )
        scan = self.make_tone(0.72, self.scan_wave)
        waste = self.make_noise_tone(0.48, self.waste_wave, seed=151)
        notebook = self.make_noise_tone(0.24, self.notebook_wave, seed=315)
        correct = self.make_tone(0.68, self.correct_wave)
        incorrect = self.make_tone(0.52, self.incorrect_wave)
        door = self.make_noise_tone(0.95, self.door_wave, seed=151151)

        sounds = {
            "button": (click, 0.52),
            "card_select": (card, 0.58),
            "scan": (scan, 0.72),
            "waste": (waste, 0.32),
            "notebook": (notebook, 0.30),
            "correct": (correct, 0.82),
            "incorrect": (incorrect, 0.74),
            "door": (door, 0.52),
        }
        for sound, relative_volume in sounds.values():
            sound.set_volume(self.sfx_volume * relative_volume)
        return {name: sound for name, (sound, _volume) in sounds.items()}

    def make_tone(self, duration, wave):
        """Build a stereo Pygame sound from a deterministic waveform function."""

        mixer_settings = pygame.mixer.get_init() or (44100, -16, 2)
        sample_rate, _sample_format, channels = mixer_settings
        frames = max(1, round(sample_rate * duration))
        samples = array("h")
        for frame in range(frames):
            t = frame / sample_rate
            value = max(-1.0, min(1.0, wave(t, duration)))
            sample = round(value * 32767)
            for _channel in range(channels):
                samples.append(sample)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def make_noise_tone(self, duration, wave, seed):
        """Build a deterministic noise-based sound for paper, waste, and doors."""

        noise = random.Random(seed)
        return self.make_tone(
            duration,
            lambda t, total: wave(t, total, noise.uniform(-1.0, 1.0)),
        )

    @staticmethod
    def sound_envelope(t, duration, attack=0.01, release=0.08):
        """Return a short attack/release envelope that prevents audible pops."""

        attack_level = min(1.0, t / max(attack, 0.0001))
        release_level = min(1.0, max(0.0, duration - t) / max(release, 0.0001))
        return attack_level * release_level

    def scan_wave(self, t, duration):
        """Return a rising electronic sweep for active diagnostic machines."""

        progress = t / duration
        phase = 2 * math.pi * (210 * t + 520 * t * t)
        pulse = 0.72 + 0.28 * math.sin(2 * math.pi * 8 * t)
        return 0.25 * self.sound_envelope(t, duration, 0.03, 0.12) * pulse * math.sin(phase)

    def waste_wave(self, t, duration, noise):
        """Return a quick card whoosh followed by a soft medical-bin thump."""

        progress = t / duration
        whoosh = noise * 0.24 * math.sin(math.pi * min(1.0, progress * 1.55))
        thump_time = max(0.0, t - duration * 0.70)
        thump = 0.0
        if thump_time > 0:
            thump = 0.40 * math.exp(-18 * thump_time) * math.sin(2 * math.pi * 92 * thump_time)
        return self.sound_envelope(t, duration, 0.01, 0.05) * (whoosh + thump)

    def notebook_wave(self, t, duration, noise):
        """Return a quiet page-flip rustle without the previous bright chime."""

        progress = t / duration
        flutter = noise * 0.10 * math.sin(math.pi * progress)
        page_lift = 0.045 * math.sin(2 * math.pi * 185 * t)
        return self.sound_envelope(t, duration, 0.008, 0.07) * (flutter + page_lift)

    def correct_wave(self, t, duration):
        """Return a compact ascending three-note success arpeggio."""

        notes = (523.25, 659.25, 783.99)
        segment = duration / len(notes)
        note_index = min(len(notes) - 1, int(t / segment))
        local_t = t - note_index * segment
        note_envelope = self.sound_envelope(local_t, segment, 0.012, 0.09)
        return 0.30 * note_envelope * math.sin(2 * math.pi * notes[note_index] * local_t)

    def incorrect_wave(self, t, duration):
        """Return a soft descending alert that communicates an incorrect diagnosis."""

        progress = t / duration
        frequency = 310 - 155 * progress
        tremolo = 0.70 + 0.30 * math.sin(2 * math.pi * 7 * t)
        return (
            0.30
            * self.sound_envelope(t, duration, 0.015, 0.12)
            * tremolo
            * math.sin(2 * math.pi * frequency * t)
        )

    def door_wave(self, t, duration, noise):
        """Return a hydraulic elevator hiss with a small arrival tone."""

        progress = t / duration
        hiss = noise * 0.11 * math.sin(math.pi * progress)
        motor = 0.13 * math.sin(2 * math.pi * (82 + 28 * progress) * t)
        ding_time = t - duration * 0.68
        ding = 0.0
        if ding_time > 0:
            ding = 0.23 * math.exp(-4.8 * ding_time) * math.sin(2 * math.pi * 880 * ding_time)
        return self.sound_envelope(t, duration, 0.025, 0.08) * (hiss + motor + ding)

    def play_sfx(self, name):
        """Play one named effect when audio is available and not muted."""

        if not self.audio_available or self.audio_muted:
            return
        sound = self.sound_effects.get(name)
        if sound is not None:
            sound.play()

    def toggle_audio_muted(self):
        """Mute or restore both the music and all sound effects."""

        if not self.audio_available:
            return
        self.audio_muted = not self.audio_muted
        if self.audio_muted:
            pygame.mixer.stop()
            pygame.mixer.music.set_volume(0.0)
        else:
            pygame.mixer.music.set_volume(self.music_volume)
            self.play_sfx("button")

    def draw_audio_button(self):
        """Draw a compact global sound toggle in the upper-left corner."""

        rect = self.audio_button
        hovered = rect.collidepoint(self.get_mouse_position())
        active_color = (232, 211, 242)
        border = (206, 158, 233) if hovered else (155, 116, 190)
        fill = (50, 37, 68) if hovered else (27, 29, 45)
        pygame.draw.rect(self.screen, (3, 8, 13), rect.move(2, 3), border_radius=8)
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen, border, rect, width=2, border_radius=8)

        speaker_x = rect.x + 13
        speaker_y = rect.centery
        pygame.draw.polygon(
            self.screen,
            active_color,
            (
                (speaker_x, speaker_y - 4),
                (speaker_x + 5, speaker_y - 4),
                (speaker_x + 10, speaker_y - 9),
                (speaker_x + 10, speaker_y + 9),
                (speaker_x + 5, speaker_y + 4),
                (speaker_x, speaker_y + 4),
            ),
        )
        if self.audio_muted:
            pygame.draw.line(
                self.screen,
                active_color,
                (speaker_x + 14, speaker_y - 6),
                (speaker_x + 24, speaker_y + 6),
                width=2,
            )
            pygame.draw.line(
                self.screen,
                active_color,
                (speaker_x + 24, speaker_y - 6),
                (speaker_x + 14, speaker_y + 6),
                width=2,
            )
        else:
            pygame.draw.arc(
                self.screen,
                active_color,
                pygame.Rect(speaker_x + 6, speaker_y - 8, 18, 16),
                -math.pi / 3,
                math.pi / 3,
                width=2,
            )

        label = self.card_font.render(
            "SOUND OFF" if self.audio_muted else "SOUND ON",
            True,
            active_color,
        )
        self.screen.blit(label, label.get_rect(midleft=(rect.x + 43, rect.centery)))
