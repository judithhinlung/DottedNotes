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

package org.codeperception.dottednotes.parsers.musicxml;

import java.io.File;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import junit.framework.TestCase;
import org.codeperception.dottednotes.math.Fraction;
import org.codeperception.dottednotes.music.*;
import org.junit.Test;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;

public class NoteTest extends TestCase {

  //~ Static fields/initializers
  private Document document;
  private Element root;

  //~ Methods ------------------------------------------------------------------------------------
  Element createMiddleC() {
    Element noteElement = document.createElement("note");
    root.appendChild(noteElement);
    Element pitchElement = document.createElement("pitch");
    noteElement.appendChild(pitchElement);
    Element octaveElement = document.createElement("octave");
    pitchElement.appendChild(octaveElement);
    Element stepElement = document.createElement("step");
    pitchElement.appendChild(stepElement);
    octaveElement.appendChild(document.createTextNode("4"));
    stepElement.appendChild(document.createTextNode("C"));
    return noteElement;
  }

  //------//
  // main //
  //------//
  //-------//
  // setUp //
  //-------//
  @Override
  protected void setUp() throws Exception {
    DocumentBuilderFactory builderFactory = DocumentBuilderFactory.newInstance();
    document = builderFactory.newDocumentBuilder().newDocument();
    root = document.createElement("root");
    document.appendChild(root);
  }

  //-----------------//
  //-------//
  // tearDown //
  //-------//
  @Override
  protected void tearDown() throws Exception {
    document = null;
    root = null;
  }

  //-----------------//
  // checkNoteParsing //
  //-----------------//
  public void testNoteParsing() throws ParserConfigurationException {
    Element noteElement = createMiddleC();
    noteElement.appendChild(document.createElement("grace"));
    Element durationElement = document.createElement("duration");
    durationElement.appendChild(document.createTextNode("24"));
    noteElement.appendChild(durationElement);
    Element instrumentElement = document.createElement("instrument");
    instrumentElement.setAttribute("id", "1");
    noteElement.appendChild(instrumentElement);
    Part part = new Part("p1");
    Measure measure = new Measure(part, 1);
    measure.setDivisions(24);
    Note note = XMLToScore.parseNote(measure, noteElement);
    assertEquals(4, note.getPitch().getOctave());
    assertEquals(0, note.getPitch().getStep());
    assertEquals(0, note.getPitch().getAlter());
    assertNotNull(note.getGrace());
    assertEquals(note.getDuration(), new Fraction(1, 4));
    assertEquals(note.getInstrumentId(), "1");
  }

  public void NotationsTest() throws ParserConfigurationException {
    Element noteElement = createMiddleC();
    Element notationsElement = document.createElement("notations");
    noteElement.appendChild(notationsElement);
    Element slurElement = document.createElement("slur");
    slurElement.setAttribute("type", "start");
    notationsElement.appendChild(slurElement);
    Element ornamentsElement = document.createElement("ornaments");
    notationsElement.appendChild(ornamentsElement);
    Element turnElement = document.createElement("turn");
    Element delayedTurnElement = document.createElement("delayed-turn");
    Element unknownElement = document.createElement("unknown-ornament");
    ornamentsElement.appendChild(turnElement);
    ornamentsElement.appendChild(delayedTurnElement);
    ornamentsElement.appendChild(unknownElement);
    Element articulationsElement = document.createElement("articulations");
    noteElement.appendChild(articulationsElement);
    Element accentElement = document.createElement("accent");
    articulationsElement.appendChild(accentElement);
    Element technicalsElement = document.createElement("technical");
    notationsElement.appendChild(technicalsElement);
    Element upbowElement = document.createElement("up-bow");
    Element fingeringElement = document.createElement("fingering");
    fingeringElement.appendChild(document.createTextNode("2"));
    technicalsElement.appendChild(upbowElement);
    technicalsElement.appendChild(fingeringElement);
    Part part = new Part("p1");
    Measure measure = new Measure(part, 1);
    Note note = XMLToScore.parseNote(measure, noteElement);
    assertEquals(null, note.getTie());
    assertNotNull(note.getSlur());
    assertEquals("start", note.getSlur().getTypes().get(0));
    assertTrue(note.getOrnaments().contains("turn"));
    assertTrue(note.getOrnaments().contains("delayedTurn"));
    assertFalse(note.getOrnaments().contains("unknown"));
    assertTrue(note.getArticulations().contains("accent"));
    assertTrue(note.getTechnical().contains("upBow"));
    assertEquals(note.getFingering(), 2);
  }

  //-----------------//
  // checkRestParsing //
  //-----------------//
  public void testRestParsing() throws ParserConfigurationException {
    Element noteElement = document.createElement("note");
    root.appendChild(noteElement);
    Element restElement = document.createElement("rest");
    restElement.setAttribute("measure", "yes");
    noteElement.appendChild(restElement);
    Element durationElement = document.createElement("duration");
    durationElement.appendChild(document.createTextNode("24"));
    noteElement.appendChild(durationElement);

    Part part = new Part("p1");
    Measure measure = new Measure(part, 1);
    Note note = XMLToScore.parseNote(measure, noteElement);
    assertNotNull(note.getPitch());
    assertTrue(note.getPitch().getIsMeasureRest());
  }
}
