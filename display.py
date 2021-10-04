#!/usr/bin/env python3

import cairo
import math
import mido
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from enum import Enum
from threading import Thread


class Key(Enum):

    Csmajor = -7
    Fsmajor = -6
    Bmajor = -5
    Emajor = -4
    Amajor = -3
    Dmajor = -2
    Gmajor = -1
    Cmajor = 0
    Fmajor = 1
    Bbmajor = 2
    Ebmajor = 3
    Abmajor = 4
    Dbmajor = 5
    Gbmajor= 6
    Cbmajor = 7

    def major_name(self):
        if self == Key.Csmajor:
            return "C# major"
        elif self == Key.Fsmajor:
            return "F# major"
        elif self == Key.Bmajor:
            return "B major"
        elif self == Key.Emajor:
            return "E major"
        elif self == Key.Amajor:
            return "A major"
        elif self == Key.Dmajor:
            return "D major"
        elif self == Key.Gmajor:
            return "G major"
        elif self == Key.Cmajor:
            return "C major"
        elif self == Key.Fmajor:
            return "F major"
        elif self == Key.Bbmajor:
            return "Bb major"
        elif self == Key.Ebmajor:
            return "Eb major"
        elif self == Key.Abmajor:
            return "Ab major"
        elif self == Key.Dbmajor:
            return "Db major"
        elif self == Key.Gbmajor:
            return "Gb major"
        elif self == Key.Cbmajor:
            return "Cb major"

    def minor_name(self):
        if self == Key.Csmajor:
            return "A# minor"
        elif self == Key.Fsmajor:
            return "D# minor"
        elif self == Key.Bmajor:
            return "G# minor"
        elif self == Key.Emajor:
            return "C# minor"
        elif self == Key.Amajor:
            return "F# minor"
        elif self == Key.Dmajor:
            return "B minor"
        elif self == Key.Gmajor:
            return "E minor"
        elif self == Key.Cmajor:
            return "A minor"
        elif self == Key.Fmajor:
            return "D minor"
        elif self == Key.Bbmajor:
            return "G minor"
        elif self == Key.Ebmajor:
            return "C minor"
        elif self == Key.Abmajor:
            return "F minor"
        elif self == Key.Dbmajor:
            return "Bb minor"
        elif self == Key.Gbmajor:
            return "Eb minor"
        elif self == Key.Cbmajor:
            return "Ab minor"


class MidiListener(Thread):

    def __init__(self):
        super().__init__(daemon=True)
        self._subscribers = set()
        self._midi_in_port = mido.open_input()

    def set_input(self, name):
        print("change input to %s" % name)
        self._midi_in_port.close()
        print(self._midi_in_port.closed)
        self._midi_in_port = mido.open_input(name)

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    def unsubscribe(self, subscriber):
        self._subscribers.remove(subscriber)

    def run(self):
        for msg in self._midi_in_port:
            print("some note")
            if msg.type == 'note_on':
                for s in self._subscribers:
                    s.on_note_played(msg.note)
            elif msg.type == 'note_off':
                for s in self._subscribers:
                    s.on_note_stopped(msg.note)
        print("end reached")


class AppWindow(Gtk.Window):

    _notes = set()

    _octave = 0

    _transpose = 0

    _midi_channel_button = Gtk.Button(label="Midi input channel")

    _key_store = Gtk.ListStore(int, str)

    _key_combo = Gtk.ComboBox()

    _transpose_button = Gtk.SpinButton(adjustment=Gtk.Adjustment(value=0, lower=-11, upper=11, step_increment=1))

    _octave_button = Gtk.SpinButton(adjustment=Gtk.Adjustment(value=0, lower=-3, upper=3, step_increment=1))

    _drawing_area = Gtk.DrawingArea(expand=True)

    _treble_png = cairo.ImageSurface.create_from_png("treble.png")

    _bass_png = cairo.ImageSurface.create_from_png("bass.png")

    _flat_png = cairo.ImageSurface.create_from_png("flat.png")

    _sharp_png = cairo.ImageSurface.create_from_png("sharp.png")

    _natural_png = cairo.ImageSurface.create_from_png("natural.png")

    def __init__(self, midi_listener):
        super().__init__(title="Note display")
        self._midi_listener = midi_listener
        self.connect("destroy", Gtk.main_quit)
        grid = Gtk.Grid()
        self.add(grid)
        # midi input channel
        grid.attach(self._midi_channel_button, 0, 0, 1, 1)
        self._midi_channel_button.connect('button-press-event', self.on_midi_channel_menu)
        # key selection
        for k in Key:
            self._key_store.append([k.value, k.major_name() + " - " + k.minor_name()])
        self._key_combo.set_model(self._key_store)
        cell = Gtk.CellRendererText()
        self._key_combo.pack_start(cell, True)
        self._key_combo.add_attribute(cell, 'text', 1)
        self._key_combo.set_active(7)
        grid.attach(Gtk.Label(label=" Key "), 1, 0, 1, 1)
        grid.attach(self._key_combo, 2, 0, 1, 1)
        self._key_combo.connect("changed", self.on_key_changed)
        # transpose and octave spin buttons
        grid.attach(Gtk.Label(label=" Transpose "), 3, 0, 1, 1)
        grid.attach(self._transpose_button, 4, 0, 1, 1)
        self._transpose_button.connect("value-changed", self.on_transpose_changed)
        grid.attach(Gtk.Label(label=" Octave "), 5, 0, 1, 1)
        grid.attach(self._octave_button, 6, 0, 1, 1)
        self._octave_button.connect("value-changed", self.on_octave_changed)
        # drawing area
        self._drawing_area.set_size_request(600, 600)
        grid.attach(self._drawing_area, 0, 1, 7, 1)
        self._drawing_area.connect('draw', self.draw)
        self.show_all()

    # position: an int that represents a line number
    # 0 is C4, 2 is E4, -2 is A4

    def effective_dimension(self, widget):
        return min(widget.get_allocated_width(), widget.get_allocated_height())

    def x_margin(self, widget):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        return 0 if width <= height else (width - height) // 2

    def y_margin(self, widget):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        return 0 if height <= width else (height - width) // 2

    def y_coord(self, widget, ctx, position):
        s = self.effective_dimension(widget)
        return (s // 40) * -position + (s // 2) + self.y_margin(widget)

    def draw_line(self, widget, ctx, position):
        dim = self.effective_dimension(widget)
        margin = self.x_margin(widget)
        x1 = (dim * 20 // 100) + margin
        x2 = (dim * 80 // 100) + margin
        y = self.y_coord(widget, ctx, position)
        ctx.set_source_rgb(0, 0, 0)
        ctx.new_path()
        ctx.move_to(x1, y)
        ctx.line_to(x2, y)
        ctx.stroke()

    def draw_short_line(self, widget, ctx, position):
        dim = self.effective_dimension(widget)
        margin = self.x_margin(widget)
        x1 = (dim * 56 // 100) + margin
        x2 = (dim * 74 // 100) + margin
        y = self.y_coord(widget, ctx, position)
        ctx.set_source_rgb(0, 0, 0)
        ctx.new_path()
        ctx.move_to(x1, y)
        ctx.line_to(x2, y)
        ctx.stroke()

    def draw_head(self, widget, ctx, position, x_shift=False):
        dim = self.effective_dimension(widget)
        margin = self.x_margin(widget)
        head_height = (dim * 24) // 1000
        y = self.y_coord(widget, ctx, position)
        if position == 0:
            self.draw_short_line(widget, ctx, 0)
        elif position > 11:
            end = position if position % 2 == 1 else position + 1
            for p in range(12, end, 2):
                self.draw_short_line(widget, ctx, p)
        elif position < -11:
            start = position if position % 2 == 0 else position + 1
            for p in range(start, -10, 2):
                self.draw_short_line(widget, ctx, p)
        ctx.save()
        if x_shift:
            ctx.translate((dim * 69 // 100) + margin, y)
        else:
            ctx.translate((dim * 65 // 100) + margin, y)
        ctx.rotate(-0.3)
        ctx.scale(1.5, 1)
        ctx.arc(0, 0, head_height, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()

    def draw_flat(self, widget, ctx, position):
        y = self.y_coord(widget, ctx, position)
        x_margin = self.x_margin(widget)
        dim = self.effective_dimension(widget)
        ctx.save()
        factor = dim / self._flat_png.get_height() * 0.1
        ctx.translate(dim * 56 // 100 + x_margin, y - self._flat_png.get_height() * factor * 1.5 // 2)
        ctx.scale(factor, factor)
        ctx.set_source_surface(self._flat_png, 10, 10)
        ctx.paint()
        ctx.restore()

    def draw_sharp(self, widget, ctx, position):
        y = self.y_coord(widget, ctx, position)
        x_margin = self.x_margin(widget)
        dim = self.effective_dimension(widget)
        ctx.save()
        factor = dim / self._sharp_png.get_height() * 0.1
        ctx.translate(dim * 56 // 100 + x_margin, y - self._sharp_png.get_height() * factor * 1.1 // 2)
        ctx.scale(factor, factor)
        ctx.set_source_surface(self._sharp_png, 10, 10)
        ctx.paint()
        ctx.restore()

    def draw_natural(self, widget, ctx, position):
        y = self.y_coord(widget, ctx, position)
        x_margin = self.x_margin(widget)
        dim = self.effective_dimension(widget)
        ctx.save()
        factor = dim / self._natural_png.get_height() * 0.1
        ctx.translate(dim * 57 // 100 + x_margin, y - self._natural_png.get_height() * factor * 1.1 // 2)
        ctx.scale(factor, factor)
        ctx.set_source_surface(self._natural_png, 10, 10)
        ctx.paint()
        ctx.restore()

    def draw_treble_clef(self, widget, ctx):
        dim = self.effective_dimension(widget)
        x_margin = self.x_margin(widget)
        y_margin = self.y_margin(widget)
        ctx.save()
        factor = dim / self._treble_png.get_height() * 0.37
        ctx.translate(dim * 20 // 100 + x_margin, dim * 170 // 1000 + y_margin)
        ctx.scale(factor, factor)
        ctx.set_source_surface(self._treble_png, 10, 10)
        ctx.paint()
        ctx.restore()

    def draw_bass_clef(self, widget, ctx):
        dim = self.effective_dimension(widget)
        x_margin = self.x_margin(widget)
        y_margin = self.y_margin(widget)
        ctx.save()
        factor = dim / self._bass_png.get_height() * 0.165
        ctx.translate(dim * 25 // 100 + x_margin, dim * 549 // 1000 + y_margin)
        ctx.scale(factor, factor)
        ctx.set_source_surface(self._bass_png, 10, 10)
        ctx.paint()
        ctx.restore()

    def draw_octave_transpose(self, widget, ctx):
        # TODO
        pass

    def draw_notes(self, widget, ctx):
        ctx.set_source_rgb(255,255,255)
        ctx.paint()
        ctx.set_source_rgb(0, 0, 0)
        ctx.set_line_width(self.effective_dimension(widget) * 7 // 1000)

        self.draw_treble_clef(widget, ctx)
        self.draw_bass_clef(widget, ctx)
        self.draw_octave_transpose(widget, ctx)
        for i in range(-10, 12, 2):
            if i != 0:
                self.draw_line(widget, ctx, i)
        occupied_positions = {n.position() for n in self._notes}
        for n in self._notes:
            p = n.position()
            x_shift = p % 2 == 1 and (p - 1 in occupied_positions or p + 1 in occupied_positions)
            self.draw_head(widget, ctx, p, x_shift)
            if n.has_accidental():
                self.draw_sharp(widget, ctx, p)

    def draw(self, widget, ctx):
        self.draw_notes(widget, ctx)

    def on_midi_channel_menu(self, widget, event):
        # generate menu according to currently available input channels
        menu = Gtk.Menu()
        for name in mido.get_input_names():
            menuitem = Gtk.MenuItem(label=name)
            menuitem.connect('button-press-event', self.on_midi_channel_changed)
            menu.append(menuitem)
            menuitem.show()
        menu.popup(None, None, None, None, event.button, event.time)

    def on_midi_channel_changed(self, widget, event):
        print(widget.get_label())
        self._midi_listener.set_input(widget.get_label())
        return

    def on_key_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            row_id, name = model[tree_iter][:2]
            print("Selected: ID=%d, name=%s" % (row_id, name))
        else:
            entry = combo.get_child()
            print("Entered: %s" % entry.get_text())
        self._drawing_area.queue_draw()

    def on_transpose_changed(self, spinbutton):
        untransposed = {n.transpose(-self._octave * 12 - self._transpose) for n in self._notes}
        self._transpose = spinbutton.get_value_as_int()
        self._notes = {n.transpose(self._octave * 12 + self._transpose) for n in untransposed}
        self._drawing_area.queue_draw()

    def on_octave_changed(self, spinbutton):
        untransposed = {n.transpose(-self._octave * 12 - self._transpose) for n in self._notes}
        self._octave = spinbutton.get_value_as_int()
        self._notes = {n.transpose(self._octave * 12 + self._transpose) for n in untransposed}
        self._drawing_area.queue_draw()

    def on_note_played(self, midi_number):
        note = Note.make_from_midi(midi_number + self._transpose + 12 * self._octave)
        self._notes.add(note)
        self._drawing_area.queue_draw()

    def on_note_stopped(self, midi_number):
        note = Note.make_from_midi(midi_number + self._transpose + 12 * self._octave)
        self._notes.discard(note)
        self._drawing_area.queue_draw()


class Pitch(Enum):

    C = 0
    Cs = 1
    D = 2
    Ds = 3
    E = 4
    F = 5
    Fs = 6
    G = 7
    Gs = 8
    A = 9
    As = 10
    B = 11

    def english_name(self, sharp=True):
        if self == Pitch.C:
            return "C"
        elif self == Pitch.Cs:
            if sharp:
                return "C#"
            else:
                return "Db"
        elif self == Pitch.D:
            return "D"
        elif self == Pitch.Ds:
            if sharp:
                return "D#"
            else:
                return "Eb"
        elif self == Pitch.E:
            return "E"
        elif self == Pitch.F:
            return "F"
        elif self == Pitch.Fs:
            if sharp:
                return "F#"
            else:
                return "Gb"
        elif self == Pitch.G:
            return "G"
        elif self == Pitch.Gs:
            if sharp:
                return "G#"
            else:
                return "Ab"
        elif self == Pitch.A:
            return "A"
        elif self == Pitch.As:
            if sharp:
                return "A#"
            else:
                return "Bb"
        elif self == Pitch.B:
            return "B"

    def latin_name(self, sharp=True):
        if self == Pitch.C:
            return "Do"
        elif self == Pitch.Cs:
            if sharp:
                return "Do #"
            else:
                return "Re b"
        elif self == Pitch.D:
            return "Re"
        elif self == Pitch.Ds:
            if sharp:
                return "Re #"
            else:
                return "Mi b"
        elif self == Pitch.E:
            return "Mi"
        elif self == Pitch.F:
            return "Fa"
        elif self == Pitch.Fs:
            if sharp:
                return "Fa #"
            else:
                return "Sol b"
        elif self == Pitch.G:
            return "Sol"
        elif self == Pitch.Gs:
            if sharp:
                return "Sol #"
            else:
                return "Lab"
        elif self == Pitch.A:
            return "La"
        elif self == Pitch.As:
            if sharp:
                return "La #"
            else:
                return "Si b"
        elif self == Pitch.B:
            return "Si"

    def position_shift(self, sharp=True):
        if self == Pitch.C:
            return 0
        elif self == Pitch.Cs:
            if sharp:
                return 0
            else:
                return 1
        elif self == Pitch.D:
            return 1
        elif self == Pitch.Ds:
            if sharp:
                return 1
            else:
                return 2
        elif self == Pitch.E:
            return 2
        elif self == Pitch.F:
            return 3
        elif self == Pitch.Fs:
            if sharp:
                return 3
            else:
                return 4
        elif self == Pitch.G:
            return 4
        elif self == Pitch.Gs:
            if sharp:
                return 5
            else:
                return 5
        elif self == Pitch.A:
            return 5
        elif self == Pitch.As:
            if sharp:
                return 5
            else:
                return 6
        elif self == Pitch.B:
            return 6

    def has_accidental(self):
        return self == Pitch.Cs or self == Pitch.Ds or self == Pitch.Fs or self == Pitch.Gs or self == Pitch.As

    def __str__(self):
        return self.english_name()


class Note:

    def __init__(self, pitch, octave):
        self._pitch = pitch
        self._octave = octave

    @classmethod
    def make_from_midi(cls, number):
        return Note(Pitch(number % 12), (number - 12) // 12)

    def midi_number(self):
        return (self._octave + 1) * 12 + self._pitch.value

    def transpose(self, semitones):
        return Note.make_from_midi(self.midi_number() + semitones)

    def position(self):
        return (self._octave - 4) * 7 + self._pitch.position_shift()

    def has_accidental(self):
        return self._pitch.has_accidental()

    def __str__(self):
        return self._pitch.english_name() + str(self._octave)

    def __hash__(self):
        return self.midi_number()

    def __eq__(self, other):
        return isinstance(other, Note) and self._pitch == other._pitch and self._octave == other._octave


if __name__ == "__main__":
    midi = MidiListener()
    window = AppWindow(midi)
    midi.subscribe(window)
    midi.start()
    Gtk.main()
