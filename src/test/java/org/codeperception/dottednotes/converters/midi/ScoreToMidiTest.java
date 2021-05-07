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

import java.util.ArrayList;
import javax.sound.midi.InvalidMidiDataException;
import javax.sound.midi.MetaMessage;
import javax.sound.midi.MidiEvent;
import javax.sound.midi.MidiMessage;
import javax.sound.midi.Sequence;
import javax.sound.midi.ShortMessage;
import javax.sound.midi.Track;
import junit.framework.TestCase;
import org.codeperception.dottednotes.math.Fraction;
import org.codeperception.dottednotes.music.*;
import org.junit.Test;

public class ScoreToMidiTest extends TestCase {

  //~ Methods --------------------------------------------------------
  public Score createScore() {
    Score score = new Score();
    Part p1 = new Part("p1");
    score.addPart(p1);
    Measure m1 = new Measure(p1, 1);
    m1.setDivisions(24);
    p1.addMeasure(m1);
    return score;
  }

  public boolean hasMessage(Track track, MidiMessage message, long tick) {
    for (int i = 0; i < track.size(); i++) {
      MidiEvent event = track.get(i);
      MidiMessage eventMessage = event.getMessage();
      if (event.getTick() == tick && eventMessage.equals(message)) {
        return true;
      }
    }
    return false;
  }

  //-----------------//
  // testCreateTimeSignatureMessage
  //-----------------//
  @Test
  public void testCreateTimeSignatureMessage() throws InvalidMidiDataException {
    Score score = createScore();
    Measure m1 = score.getPart("p1").getMeasure(1);
    TimeSignature time = new TimeSignature(3, 4);
    m1.setTime(time);
    ScoreToMidi midiScore = new ScoreToMidi(score);
    MetaMessage message = midiScore.createTimeSignatureMessage(time);
    assertEquals(message.getType(), 0x58);
    assertEquals(message.getData().length, 4);
    byte[] data = message.getData();
    assertEquals((int) data[0], 3);
    assertEquals((int) data[1], 4);
  }

  //-----------------//
  // testConversionFromMusicDurationsToMidiTicks
  //-----------------//
  public void testGetMidiTicks() throws InvalidMidiDataException {
    Score score = createScore();
    ScoreToMidi midiScore = new ScoreToMidi(score);
    // assertEquals(midiScore.getMidiTicks(new Fraction(1, 4)), 24);
    assertEquals(midiScore.getMidiTicks(new Fraction(1, 8)), 12);
    assertEquals(midiScore.getMidiTicks(new Fraction(1, 16)), 6);
  }

  public void testGetTicksPerMeasure() throws InvalidMidiDataException {
    Score score = createScore();
    ScoreToMidi midiScore = new ScoreToMidi(score);
    Measure m1 = score.getPart("p1").getMeasure(1);
    m1.setTime(new TimeSignature(4, 4));
    assertEquals(midiScore.getTicksPerMeasure(m1), 96);
    m1.setTime(new TimeSignature(3, 4));
    assertEquals(midiScore.getTicksPerMeasure(m1), 72);
    m1.setTime(new TimeSignature(6, 8));
    assertEquals(midiScore.getTicksPerMeasure(m1), 72);
    m1.setTime(new TimeSignature(9, 8));
    assertEquals(midiScore.getTicksPerMeasure(m1), 108);
  }

  //-----------------//
  // testAddNoteToTrack
  //-----------------//
  public void testAddNoteToTrack() throws InvalidMidiDataException {
    Score score = createScore();
    Measure m1 = score.getPart("p1").getMeasure(1);
    TimeSignature time = new TimeSignature(4, 4);
    m1.setTime(time);
    m1.setDivisions(24);
    Pitch pitch = new Pitch("p", 4, 0);
    Note note1 = new Note(m1, pitch, new Fraction(1, 4));
    pitch = new Pitch("p", 4, 2);
    Note note2 = new Note(m1, pitch, new Fraction(1, 4));
    pitch = new Pitch("p", 4, 4);
    Note note3 = new Note(m1, pitch, new Fraction(1, 4));
    pitch = new Pitch("p", 4, 5);
    Note note4 = new Note(m1, pitch, new Fraction(1, 4));
    m1.addElement(note1);
    m1.addElement(note2);
    m1.addElement(note3);
    m1.addElement(note4);
    ScoreToMidi midiScore = new ScoreToMidi(score);
    Sequence sequence = midiScore.sequence;
    Track[] tracks = sequence.getTracks();
    assertEquals(2, tracks.length);
    Track track = tracks[1];
    assertEquals(96, track.ticks());
  }
}
