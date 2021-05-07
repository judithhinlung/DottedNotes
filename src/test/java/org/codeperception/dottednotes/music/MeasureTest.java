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

package org.codeperception.dottednotes.music;

import java.util.ArrayList;
import junit.framework.TestCase;
import org.codeperception.dottednotes.math.Fraction;
import org.junit.Test;

public class MeasureTest extends TestCase {

  //-----------------//
  // testMeasureInstantiation
  //-----------------//
  @Test
  public void testMeasureInstantiation() {
    Part p1 = new Part("p1");
    Measure m1 = new Measure(p1, 1);
    assertEquals(m1.getPart().getId(), "p1");
    assertEquals(m1.getNumber(), 1);
    assertEquals(m1.getStaves().size(), 1);
  }

  public void testMeasureInstantiationWithOneStaffAndVoice() {
    Part p1 = new Part("p1");
    Measure m1 = new Measure(p1, 1);
    assertEquals(Fraction.ZERO, m1.getOffset());
    Pitch pitch = new Pitch("p", 4, 0);
    Note note1 = new Note(m1, pitch, new Fraction(1, 4));
    Note note2 = new Note(m1, pitch, new Fraction(1, 4));
    Note note3 = new Note(m1, pitch, new Fraction(1, 2));
    m1.addElement(note1);
    assertEquals(new Fraction(1, 4), m1.getOffset());
    m1.addElement(note2);
    assertEquals(new Fraction(1, 2), m1.getOffset());
    m1.addElement(note3);
    assertEquals(new Fraction(1, 1), m1.getOffset());
    assertEquals(m1.getStaves().size(), 1);
    Staff staff = m1.getStaff(1);
    assertEquals(staff.getVoices().size(), 1);
    assertTrue(staff.hasVoice(1));
    Voice voice = staff.getVoice(1);
    assertEquals(voice.getElements().size(), 3);
  }

  public void testMeasureInstantiationWithOneStaffAnMultipleVoices() {
    Part p1 = new Part("p1");
    Measure m1 = new Measure(p1, 1);
    Pitch pitch = new Pitch("p", 4, 0);
    Note note1 = new Note(m1, pitch, new Fraction(1, 4));
    Note note2 = new Note(m1, pitch, new Fraction(1, 4));
    Note note3 = new Note(m1, pitch, new Fraction(1, 2));
    m1.addElement(note1);
    assertEquals(new Fraction(1, 4), m1.getOffset());
    m1.addElement(note2);
    assertEquals(new Fraction(1, 2), m1.getOffset());
    m1.addElement(note3);
    assertEquals(new Fraction(1, 1), m1.getOffset());
    assertEquals(m1.getStaves().size(), 1);
    Staff staff = m1.getStaff(1);
    assertTrue(staff.hasVoice(1));
    Voice voice = staff.getVoice(1);
    assertEquals(voice.getElements().size(), 3);
    assertFalse(staff.hasVoice(2));
    m1.addElement(new Backup(m1, new Fraction(1, 1)));
    assertEquals(Fraction.ZERO, m1.getOffset());
    Note note4 = new Note(m1, pitch, new Fraction(1, 2));
    note4.setVoiceNumber(2);
    Note note5 = new Note(m1, pitch, new Fraction(1, 4));
    note5.setVoiceNumber(2);
    Note note6 = new Note(m1, pitch, new Fraction(1, 4));
    note6.setVoiceNumber(2);
    m1.addElement(note4);
    assertEquals(new Fraction(1, 2), m1.getOffset());
    m1.addElement(note5);
    assertEquals(new Fraction(3, 4), m1.getOffset());
    m1.addElement(note6);
    assertEquals(new Fraction(1, 1), m1.getOffset());
    assertEquals(staff.getVoices().size(), 2);
    assertTrue(staff.hasVoice(2));
  }

  public void testMeasureInstantiationWithTwoStavesAnTwoVoices() {
    Part p1 = new Part("p1");
    p1.setStaves(2);
    Measure m1 = new Measure(p1, 1);
    Pitch pitch = new Pitch("p", 4, 0);
    Note note1 = new Note(m1, pitch, new Fraction(1, 4));
    Note note2 = new Note(m1, pitch, new Fraction(1, 4));
    Note note3 = new Note(m1, pitch, new Fraction(1, 2));
    assertEquals(Fraction.ZERO, m1.getOffset());
    m1.addElement(note1);
    assertEquals(new Fraction(1, 4), m1.getOffset());
    m1.addElement(note2);
    assertEquals(new Fraction(1, 2), m1.getOffset());
    m1.addElement(note3);
    assertEquals(new Fraction(1, 1), m1.getOffset());
    m1.addElement(new Backup(m1, new Fraction(1, 1)));
    Note note4 = new Note(m1, pitch, new Fraction(1, 2));
    note4.setStaffNumber(2);
    note4.setVoiceNumber(2);
    Note note5 = new Note(m1, pitch, new Fraction(1, 4));
    note5.setStaffNumber(2);
    note5.setVoiceNumber(2);
    Note note6 = new Note(m1, pitch, new Fraction(1, 4));
    note6.setStaffNumber(2);
    note6.setVoiceNumber(2);
    m1.addElement(note4);
    assertEquals(new Fraction(1, 2), m1.getOffset());
    m1.addElement(note5);
    assertEquals(new Fraction(3, 4), m1.getOffset());
    m1.addElement(note6);
    assertEquals(new Fraction(1, 1), m1.getOffset());
    assertEquals(m1.getStaves().size(), 2);
    Staff s1 = m1.getStaff(1);
    Staff s2 = m1.getStaff(2);
    assertTrue(s1.hasVoice(1));
    assertTrue(s2.hasVoice(2));
    Voice v1 = s1.getVoice(1);
    assertEquals(v1.getElements().size(), 3);
    assertTrue(s2.hasVoice(2));
    Voice v2 = s2.getVoice(2);
    assertEquals(v2.getElements().size(), 3);
  }

  public void testMeasureInstantiationWithTwoStavesAndTwoChords() {
    Part p1 = new Part("p1");
    p1.setStaves(2);
    Measure m1 = new Measure(p1, 1);
    Note note1 = new Note(m1, new Pitch("p", 4, 0), new Fraction(1, 4));
    Note note2 = new Note(m1, new Pitch("p", 4, 2), new Fraction(1, 4));
    Note note3 = new Note(m1, new Pitch("p", 4, 4), new Fraction(1, 2));
    Chord c1 = new Chord(m1);
    c1.addNote(note1);
    c1.addNote(note2);
    c1.addNote(note3);
    c1.setDuration(new Fraction(1, 4));
    assertEquals(new Fraction(1, 4), c1.getDuration());
    m1.addElement(c1);
    assertEquals(new Fraction(1, 4), m1.getOffset());
    Note note4 = new Note(m1, new Pitch("p", 5, 0), new Fraction(1, 2));
    note4.setStaffNumber(2);
    note4.setVoiceNumber(2);
    Note note5 = new Note(m1, new Pitch("p", 5, 2), new Fraction(1, 4));
    note5.setStaffNumber(2);
    note5.setVoiceNumber(2);
    Note note6 = new Note(m1, new Pitch("p", 6, 0), new Fraction(1, 4));
    note6.setStaffNumber(2);
    note6.setVoiceNumber(2);
    m1.addElement(new Backup(m1, new Fraction(1, 4)));
    Chord c2 = new Chord(m1);
    c2.addNote(note4);
    c2.addNote(note5);
    c2.addNote(note6);
    c2.setDuration(new Fraction(1, 4));
    m1.addElement(c2);
    assertEquals(new Fraction(1, 4), m1.getOffset());
    assertEquals(m1.getStaves().size(), 2);
    Staff s1 = m1.getStaff(1);
    Staff s2 = m1.getStaff(2);
    assertTrue(s1.hasVoice(1));
    // assertTrue(s2.hasVoice(2));
    assertEquals(2, c2.getVoiceNumber());
    Voice v1 = s1.getVoice(1);
    assertEquals(v1.getElements().size(), 1);
    assertTrue(s2.hasVoice(2));
    Voice v2 = s2.getVoice(2);
    assertEquals(v2.getElements().size(), 1);
  }

  //-----------------//
  // TestRemoveMeasureElements
  //-----------------//
  public void testRemoveNote() {
    Part p1 = new Part("p1");
    p1.setStaves(1);
    Measure m1 = new Measure(p1, 1);
    Note note1 = new Note(m1, new Pitch("p", 4, 0), new Fraction(1, 4));
    Note note2 = new Note(m1, new Pitch("p", 4, 2), new Fraction(1, 4));
    Note note3 = new Note(m1, new Pitch("p", 4, 4), new Fraction(1, 2));
    m1.addElement(note1);
    m1.addElement(note2);
    m1.addElement(note3);
    assertEquals(new Fraction(1, 1), m1.getOffset());
    Voice v1 = m1.getStaff(1).getVoice(1);
    assertEquals(v1.getElements().size(), 3);
    m1.removeElement(note3);
    assertEquals(new Fraction(1, 2), m1.getOffset());
    // assertEquals(v1.getElements().size(), 2);
    m1.removeElement(note1);
    assertEquals(new Fraction(1, 4), m1.getOffset());
    assertEquals(note2.getMoment(), Fraction.ZERO);
  }

  public void testRemoveChord() {
    Part p1 = new Part("p1");
    p1.setStaves(1);
    Measure m1 = new Measure(p1, 1);
    Note note1 = new Note(m1, new Pitch("p", 4, 0), new Fraction(1, 4));
    Note note2 = new Note(m1, new Pitch("p", 4, 2), new Fraction(1, 4));
    Chord c1 = new Chord(m1);
    c1.addNote(note1);
    c1.addNote(note2);
    c1.setDuration(new Fraction(1, 4));
    m1.addElement(c1);
    Note note3 = new Note(m1, new Pitch("p", 4, 0), new Fraction(1, 2));
    Note note4 = new Note(m1, new Pitch("p", 4, 2), new Fraction(1, 2));
    Chord c2 = new Chord(m1);
    c2.addNote(note3);
    c2.addNote(note4);
    c2.setDuration(new Fraction(1, 2));
    m1.addElement(c2);
    Note note5 = new Note(m1, new Pitch("p", 4, 0), new Fraction(1, 4));
    Note note6 = new Note(m1, new Pitch("p", 4, 2), new Fraction(1, 4));
    Note note7 = new Note(m1, new Pitch("p", 4, 4), new Fraction(1, 4));
    Chord c3 = new Chord(m1);
    c3.addNote(note5);
    c3.addNote(note6);
    c3.addNote(note7);
    c3.setDuration(new Fraction(1, 4));
    m1.addElement(c3);
    Voice v1 = m1.getStaff(1).getVoice(1);
    assertEquals(v1.getElements().size(), 3);
    assertEquals(new Fraction(1, 1), m1.getOffset());
    m1.removeElement(c3);
    assertEquals(new Fraction(3, 4), m1.getOffset());
    assertEquals(v1.getElements().size(), 2);
    m1.removeElement(c1);
    assertEquals(new Fraction(1, 2), m1.getOffset());
    assertEquals(v1.getElements().size(), 1);
    assertEquals(c2.getMoment(), Fraction.ZERO);
  }

  //-----------------//
  // TestReturnsCorrectKeyAndTimeSignatures
  //-----------------//
  public void testReturnsCorrectKeyAndTimeWhenSpecifiedWithinMeasure() {
    Part p1 = new Part("p1");
    Measure m1 = new Measure(p1, 1);
    KeySignature key = new KeySignature(1);
    TimeSignature time = new TimeSignature(4, 4);
    m1.setKey(key);
    m1.setTime(time);
    assertEquals(m1.getKey().getType(), 1);
    assertEquals(m1.getTime(), new Fraction(4, 4));
  }

  public void testReturnsCorrectKeyAndTimeWhenSpecifiedInPreviousMeasure() {
    Part p1 = new Part("p1");
    Measure m1 = new Measure(p1, 1);
    KeySignature key = new KeySignature(1);
    TimeSignature time = new TimeSignature(4, 4);
    m1.setKey(key);
    m1.setTime(time);
    Measure m2 = new Measure(p1, 2);
    assertEquals(m2.getKey().getType(), 1);
    assertEquals(m2.getTime(), new Fraction(4, 4));
  }

  public void testReturnsCorrectKeyAndTimeWithKeyChange() {
    Part p1 = new Part("p1");
    Measure m1 = new Measure(p1, 1);
    m1.setKey(new KeySignature(-1));
    m1.setTime(new TimeSignature(4, 4));
    Measure m2 = new Measure(p1, 2);
    m2.setKey(new KeySignature(1));
    m2.setTime(new TimeSignature(3, 4));
    Measure m3 = new Measure(p1, 3);
    assertEquals(m3.getKey().getType(), 1);
    assertEquals(m3.getTime(), new Fraction(3, 4));
  }

  //-----------------//
  // TestCalculateDivisionsPerQuarterNoteFromMusicDurations
  //-----------------//
  public void testCalculateDivisions() {
    Part p1 = new Part("p1");
    Measure m1 = new Measure(p1, 1);
    Pitch pitch = new Pitch("p", 4, 0);
    Note note1 = new Note(m1, pitch, new Fraction(1, 4));
    Note note2 = new Note(m1, pitch, new Fraction(1, 4));
    Note note3 = new Note(m1, pitch, new Fraction(1, 4));
    Note note4 = new Note(m1, pitch, new Fraction(1, 4));
    Note note5 = new Note(m1, pitch, new Fraction(1, 16));
    Note note6 = new Note(m1, pitch, new Fraction(1, 4));
    m1.addElement(note1);
    m1.addElement(note2);
    m1.addElement(note3);
    m1.addElement(note4);
    m1.addElement(note5);
    m1.addElement(note6);
    assertEquals(m1.getStaves().size(), 1);
    Staff staff = m1.getStaff(1);
    assertEquals(staff.getVoices().size(), 1);
    assertTrue(staff.hasVoice(1));
    Voice voice = staff.getVoice(1);
    // assertEquals(voice.getElements().size(), 6);
    assertEquals(m1.calculateDivisions(), 4);
  }

  public void testCalculateDivisionsWithTimeModification() {
    Part p1 = new Part("p1");
    Measure m1 = new Measure(p1, 1);
    Pitch pitch = new Pitch("p", 4, 0);
    Note note1 = new Note(m1, pitch, new Fraction(1, 4));
    Note note2 = new Note(m1, pitch, new Fraction(1, 4));
    Note note3 = new Note(m1, pitch, new Fraction(1, 4));
    note3.setTimeModification(new TimeModification(2, 3));
    Note note4 = new Note(m1, pitch, new Fraction(1, 4));
    note4.setTimeModification(new TimeModification(2, 3));
    Note note5 = new Note(m1, pitch, new Fraction(1, 4));
    note5.setTimeModification(new TimeModification(2, 3));
    m1.addElement(note1);
    m1.addElement(note2);
    m1.addElement(note3);
    m1.addElement(note4);
    m1.addElement(note5);
    ArrayList<Fraction> durations = m1.getDurationsList();
    assertEquals(m1.calculateDivisions(), 3);
  }

  //-----------------//
  // CheckForCompleteMeasure
  //-----------------
  public void checkCompleteMeasureWithSimpleTime() {
    Part p1 = new Part("p1");
    Measure m1 = new Measure(p1, 1);
    m1.setTime(new TimeSignature(4, 4));
    Pitch pitch = new Pitch("p", 3, 4);
    Note note1 = new Note(m1, pitch, new Fraction(1, 4));
    Note note2 = new Note(m1, pitch, new Fraction(1, 4));
    Note note3 = new Note(m1, pitch, new Fraction(1, 4));
    m1.addElement(note1);
    m1.addElement(note2);
    m1.addElement(note3);
    assertFalse(m1.isCompleteMeasure()); //
    Note note4 = new Note(m1, pitch, new Fraction(1, 8));
    Note note5 = new Note(m1, pitch, new Fraction(1, 8));
    assertTrue(m1.isCompleteMeasure());
  }

  public void checkCompleteMeasureWithCompoundTime() {
    Part p1 = new Part("p1");
    Measure m1 = new Measure(p1, 1);
    m1.setTime(new TimeSignature(6, 8));
    Pitch pitch = new Pitch("p", 3, 4);
    Note note1 = new Note(m1, pitch, new Fraction(1, 4));
    Note note2 = new Note(m1, pitch, new Fraction(1, 4));
    Note note3 = new Note(m1, pitch, new Fraction(1, 8));
    m1.addElement(note1);
    m1.addElement(note2);
    m1.addElement(note3);
    assertFalse(m1.isCompleteMeasure()); //
    Note note4 = new Note(m1, pitch, new Fraction(1, 8));
    assertTrue(m1.isCompleteMeasure());
  }

  //-----------------//
  // CheckMeasureElementsSorting
  //-----------------
  public void checkMeasureElementSortingWithOneStaff() {
    Part p1 = new Part("p1");
    Measure m1 = new Measure(p1, 1);
    m1.setTime(new TimeSignature(4, 4));
    Note note1 = new Note(m1, new Pitch("p", 3, 4), new Fraction(1, 4));
    Note note2 = new Note(m1, new Pitch("p", 3, 6), new Fraction(1, 4));
    Note note3 = new Note(m1, new Pitch("p", 3, 4), new Fraction(2, 4));
    m1.addElement(note1);
    m1.addElement(note2);
    m1.addElement(note3);
    ArrayList<MeasureElement> elements = m1.getMeasureElements();
    assertEquals(elements.get(0), note1);
    assertEquals(elements.get(2), note3);
  }

  public void checkMeasureElementSortingWithTwoStaves() {
    Part p1 = new Part("p1");
    Measure m1 = new Measure(p1, 1);
    m1.setTime(new TimeSignature(4, 4));
    Note note1 = new Note(m1, new Pitch("p", 3, 4), new Fraction(1, 4));
    Note note2 = new Note(m1, new Pitch("p", 3, 6), new Fraction(1, 4));
    Note note3 = new Note(m1, new Pitch("p", 3, 4), new Fraction(2, 4));
    Note note4 = new Note(m1, new Pitch("p", 2, 4), new Fraction(1, 4));
    Note note5 = new Note(m1, new Pitch("p", 2, 6), new Fraction(1, 4));
    Note note6 = new Note(m1, new Pitch("p", 2, 4), new Fraction(2, 4));
    note4.setStaffNumber(2);
    note5.setStaffNumber(2);
    note6.setStaffNumber(2);
    m1.addElement(note1);
    m1.addElement(note2);
    m1.addElement(note3);
    m1.addElement(note4);
    m1.addElement(note5);
    m1.addElement(note6);
    ArrayList<MeasureElement> elements = m1.getMeasureElements();
    assertEquals(elements.get(0), note1);
    assertEquals(elements.get(1), note4);
    assertEquals(elements.get(5), note3);
    assertEquals(elements.get(6), note6);
  }
}
