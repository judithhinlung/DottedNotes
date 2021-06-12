/**
 * DottedNotes: -- Braille Music Conversion Utility
 *
 * Copyright 2021 Judith Lung  All Rights Reserved.
 *
 * This code is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License version 3, as
 * published by the Free Software Foundation.
 *
 * This code is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this work; if not, see <http://www.gnu.org/licenses/>.
 */

package org.codeperception.dottednotes.converters.midi;

import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import javax.sound.midi.InvalidMidiDataException;
import javax.sound.midi.MetaMessage;
import javax.sound.midi.MidiEvent;
import javax.sound.midi.MidiSystem;
import javax.sound.midi.Sequence;
import javax.sound.midi.ShortMessage;
import javax.sound.midi.Track;
import org.codeperception.dottednotes.math.Fraction;
import org.codeperception.dottednotes.music.*;

public class ScoreToMidi {

  Score score;
  Sequence sequence;
  Track tempoTrack;
  boolean unroll = false;

  public ScoreToMidi(Score score) throws InvalidMidiDataException {
    this.score = score;
    this.sequence = new Sequence(Sequence.PPQ, score.getDivisions());
    this.tempoTrack = sequence.createTrack();
    addTracksFromScore(score);
  }

  /** Setting unroll to true indicates that
   * repeats and endings should be represented.
   */
  public ScoreToMidi(Score score, boolean unroll) throws InvalidMidiDataException {
    this.score = score;
    this.sequence = new Sequence(Sequence.PPQ, score.getDivisions());
    this.tempoTrack = sequence.createTrack();
    this.unroll = unroll;
    addTracksFromScore(score);
  }

  public Sequence getSequence() {
    return this.sequence;
  }

  private int velocity = 64;

  void addTracksFromScore(Score score) throws InvalidMidiDataException {
    ArrayList<Part> parts = score.getParts();
    for (int i = 0; i < parts.size(); i++) {
      Part part = parts.get(i);
      createTrackFromPart(part);
    }
  }

  void createTrackFromPart(Part part) throws InvalidMidiDataException {
    Track track = sequence.createTrack();
    int ticks = 0;
    int backwardRepeat = -1;
    int forwardRepeat = -1;
    int times = 1;
    if (part.getName() != null) {
      MetaMessage Mt = new MetaMessage();
      track.add(TextMessage.TrackName.createEvent(part.getName(), 0));
    }
    ArrayList<Instrument> instruments = part.getInstruments();
    Instrument instrument = null;
    if (instruments.size() > 0) {
      instrument = instruments.get(0);
    } else {
      instrument = new Instrument(part.getId());
    }
    try {
      setMidiInstrument(instrument, track, 0);
    } catch (InvalidMidiDataException e) {
      e.printStackTrace();
    }
    int round = 1;
    ArrayList<Measure> measures = part.getMeasures();
    for (int current = 0; current < measures.size(); current++) {
      Measure measure = measures.get(current);
      ArrayList<MeasureElement> elements = measure.getMeasureElements();
      for (int i = 0; i < elements.size(); i++) {
        MeasureElement element = elements.get(i);
        Fraction nextMoment = getNextMoment(i, elements);
        if (element instanceof Note) {
          Note note = (Note) element;
          addNoteToTrack(note, track, ticks);
          ticks += getMidiTicks(nextMoment);
        } else if (element instanceof Chord) {
          Chord chord = (Chord) element;
          ArrayList<Note> notes = chord.getNotes();
          for (int j = 0; j < notes.size(); j++) {
            Note note = notes.get(j);
            addNoteToTrack(note, track, ticks);
          }
          ticks += getMidiTicks(nextMoment);
        } else if (element instanceof Pedal) {
          Pedal pedal = (Pedal) element;
          boolean press = false;
          if (pedal.getType().equals("start")) {
            press = true;
          }
          track.add(new MidiEvent(createPedalMessage(0, press), ticks));
        } else if (element instanceof Barline) {
          Barline barline = (Barline) element;
          if (unroll) {
            if (barline.getRepeat() != null) {
              Repeat repeat = barline.getRepeat();
              if (repeat.getDirection().equals("forward")) {
                if (round == 1) {
                  forwardRepeat = current;
                } else if (round > times + 1) {
                  forwardRepeat = -1;
                }
              } else if (repeat.getDirection().equals("backward")) {
                if (round == 1) {
                  current = forwardRepeat;
                  round += 1;
                } else if (round > times + 1) {
                  backwardRepeat = -1;
                  round = 1;
                }
              }
            }
            if (barline.getEnding() != null) {
              if (barline.isEndingStart() && barline.getEnding().getNumber() < round) {
                int endingStopMeasure = getLastMeasureOfEnding(
                  barline.getEnding().getNumber(),
                  current,
                  part
                );
                current = endingStopMeasure + 1;
              }
            }
          }
        } else if (element instanceof Sound) {
          Sound sound = (Sound) element;
          convertSound(sound, track, ticks);
        }
      }
    }
  }

  private Fraction getNextMoment(int index, ArrayList<MeasureElement> elements) {
    Fraction nextMoment = Fraction.ZERO;
    MeasureElement element = elements.get(index);
    if (index < elements.size() - 1) {
      MeasureElement nextElement = elements.get(index + 1);
      nextMoment = nextElement.getMoment().subtract(element.getMoment());
    } else {
      nextMoment = element.getDuration();
    }
    return nextMoment;
  }

  public int getLastMeasureOfEnding(int ending, int measureNumber, Part part) {
    ArrayList<Measure> measures = part.getMeasures();
    Measure startMeasure = part.getMeasure(measureNumber);
    int startMeasureIndex = measures.indexOf(startMeasure);
    for (int i = startMeasureIndex; i < measures.size(); i++) {
      Measure measure = measures.get(i);
      ArrayList<MeasureElement> elements = measure.getMeasureElements();
      for (int j = elements.size() - 1; j >= 0; j--) {
        MeasureElement element = elements.get(i);
        if (element instanceof Barline) {
          Barline barline = (Barline) element;
          if (
            barline.getLocation().equals("right") &&
            barline.getEnding().getType().equals("stop")
          ) {
            return measure.getNumber();
          }
        }
      }
    }
    return -1;
  }

  void setMidiInstrument(Instrument instrument, Track track, int tick)
    throws InvalidMidiDataException {
    int channel = instrument.getMidiChannel();
    int program = instrument.getMidiProgram();
    ShortMessage msg = new ShortMessage();
    msg.setMessage(ShortMessage.PROGRAM_CHANGE, channel, program, 0);
    track.add(new MidiEvent(msg, tick));
  }

  void addNoteToTrack(Note note, Track track, int tick) throws InvalidMidiDataException {
    if (note.getLyric() != null) {
      String text = note.getLyric().getText();
      track.add(TextMessage.Lyric.createEvent(text, tick));
    }
    Pitch pitch = note.getPitch();
    int duration = getMidiTicks(note.getDuration());
    ArrayList<Articulation> articulations = note.getArticulations();
    if (articulations.size() > 0) {
      for (int i = 0; i < articulations.size(); i++) {
        Articulation articulation = articulations.get(i);
        if (articulation.getType().equals("staccatissimo")) {
          duration /= 4;
        } else if (articulation.getType().equals("staccato")) {
          duration /= 2;
        }
      }
    }
    if (pitch.getType().equals("p")) {
      int midiPitch = pitch.getMidiPitch();
      int midiChannel = note.getMidiChannel();
      ArrayList<Ornament> ornaments = note.getOrnaments();
      if (note.getOrnaments().size() > 0) {
        KeySignature key = note.getMeasure().getKey();
        for (int i = 0; i < ornaments.size(); i++) {
          Ornament ornament = ornaments.get(i);
          if (ornament.getType().equals("turn")) {
            int upperPitch = pitch.getNextStep(key).getMidiPitch();
            int lowerPitch = 0;
            if (ornament.getAccidental() != null) {
              int accidental = ornament.getAccidental().getModifier();
              lowerPitch = pitch.getPreviousStep(accidental).getMidiPitch();
            } else {
              lowerPitch = pitch.getPreviousStep(key).getMidiPitch();
            }
            duration /= 4;
            noteOnOff(track, midiChannel, upperPitch, velocity, tick, duration);
            tick += duration;
            noteOnOff(track, midiChannel, midiPitch, velocity, tick, duration);
            tick += duration;
            noteOnOff(track, midiChannel, lowerPitch, velocity, tick, duration);
            tick += duration;
            noteOnOff(track, midiChannel, midiPitch, velocity, tick, duration);
            return;
          } else if (ornament.getType().equals("mordent")) {
            int lowerPitch = 0;
            if (ornament.getAccidental() != null) {
              int accidental = ornament.getAccidental().getModifier();
              lowerPitch = pitch.getPreviousStep(accidental).getMidiPitch();
            } else {
              lowerPitch = pitch.getPreviousStep(key).getMidiPitch();
            }
            duration /= 8;
            noteOnOff(track, midiChannel, midiPitch, velocity, tick, duration);
            tick += duration;
            noteOnOff(track, midiChannel, lowerPitch, velocity, tick, duration);
            tick += duration;
            noteOnOff(track, midiChannel, midiPitch, velocity, tick, duration * 6);
          }
        }
      }
      if (note.getTie() != null) {
        Tie tie = note.getTie();
        if (tie.getType().equals("start")) {
          noteOn(track, midiChannel, midiPitch, velocity, tick);
        } else if (tie.getType().equals("stop")) {
          noteOff(track, midiChannel, midiPitch, velocity, (tick + duration));
        }
      } else {
        noteOnOff(track, note.getMidiChannel(), midiPitch, velocity, tick, duration);
      }
    }
  }

  private static void noteOnOff(
    Track track,
    int channel,
    int pitch,
    int velocity,
    int tick,
    int duration
  ) throws InvalidMidiDataException {
    ShortMessage msg = new ShortMessage();
    int noteOn = 144;
    int noteOff = 128;
    msg.setMessage(noteOn, channel, pitch, velocity);
    track.add(new MidiEvent(msg, tick));
    msg = new ShortMessage();
    msg.setMessage(noteOff, channel, pitch, 0);
    track.add(new MidiEvent(msg, tick + duration));
  }

  private static void noteOn(Track track, int channel, int pitch, int velocity, int tick)
    throws InvalidMidiDataException {
    ShortMessage msg = new ShortMessage();
    int noteOn = 144;
    msg.setMessage(noteOn, channel, pitch, velocity);
    track.add(new MidiEvent(msg, tick));
  }

  private static void noteOff(
    Track track,
    int channel,
    int pitch,
    int velocity,
    int tick
  ) throws InvalidMidiDataException {
    ShortMessage msg = new ShortMessage();
    int noteOff = 128;
    msg.setMessage(noteOff, channel, pitch, 0);
    track.add(new MidiEvent(msg, tick));
  }

  void convertSound(Sound sound, Track track, int tick) throws InvalidMidiDataException {
    if (sound.getInstrument() != null) {
      Instrument instrument = sound.getInstrument();
      setMidiInstrument(instrument, track, tick);
    }
    if (sound.getVelocity() != velocity) {
      velocity = sound.getVelocity();
    }
    if (sound.getTempo() > 0) {
      MetaMessage tempoMessage = createTempoMessage(sound.getTempo());
      tempoTrack.add(new MidiEvent(tempoMessage, tick));
    }
  }

  protected enum TextMessage {
    General(1),
    Copyright(2),
    TrackName(3),
    Instrument(4),
    Lyric(5),
    Marker(6),
    CuePoint(7),
    ProgramName(8),
    DeviceName(9);

    private final int type;

    TextMessage(final int type) {
      this.type = type;
    }

    MidiEvent createEvent(final String data, int offset) throws InvalidMidiDataException {
      final MetaMessage message = new MetaMessage();
      message.setMessage(type, data.getBytes(), data.length());
      return new MidiEvent(message, offset);
    }
  }

  /** Creates a time signature metamessage, 0x58
   * @param numerator  Beats per measure
   * @param denominator  Beat unit type
   * @param cc Midi clocks per tick
   * @param nn  number of 32nd notes per quarter note
   */
  public MetaMessage createTimeSignatureMessage(TimeSignature time) {
    int numerator = time.numerator();
    int denominator = time.denominator();
    int cc = 24;
    int nn = 8;
    try {
      MetaMessage message = new MetaMessage();
      message.setMessage(
        0x58,
        new byte[] { (byte) numerator, (byte) denominator, (byte) cc, (byte) nn },
        4
      );
      return message;
    } catch (InvalidMidiDataException e) {
      e.printStackTrace();
    }
    return null;
  }

  /** Creates a tempo metamessage from a tempo specified in MeasureElement Sound
   * @return a MetaMessage or null, if no tempo attribute was found
   */
  public MetaMessage createTempoMessage(int tempo) {
    int midiTempo = Math.round((float) 60000.0 / tempo * 1000);
    final MetaMessage message = new MetaMessage();
    byte[] bytes = new byte[3];
    bytes[0] = (byte) (midiTempo / 0X10000);
    midiTempo %= 0X10000;
    bytes[1] = (byte) (midiTempo / 0X100);
    midiTempo %= 0X100;
    bytes[2] = (byte) midiTempo;
    try {
      message.setMessage(0X51, bytes, bytes.length);
      return message;
    } catch (InvalidMidiDataException e) {
      e.printStackTrace();
    }
    return null;
  }

  private static ShortMessage createPedalMessage(final int channel, final boolean press)
    throws InvalidMidiDataException {
    ShortMessage msg = new ShortMessage();
    msg.setMessage(ShortMessage.CONTROL_CHANGE, channel, 64, press ? 127 : 0);
    return msg;
  }

  int getMidiTicks(Fraction duration) {
    int divisions = this.score.getDivisions();
    int numerator = duration.numerator();
    int denominator = duration.denominator();
    return numerator * divisions * 4 / denominator;
  }

  int getTicksPerMeasure(Measure measure) {
    TimeSignature time = measure.getTime();
    int numerator = time.numerator();
    int denominator = time.denominator();
    int divisions = this.score.getDivisions();
    return numerator * divisions * 4 / denominator;
  }
}
