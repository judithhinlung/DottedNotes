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

public class Lyric {

  /**
   * @param text   lyric text
   * @param syllabic  representing  single, begin (word-beginning), middle (mid-word), end (word-ending) syllables
   * @param isExtended  indicates a word extension across multiple notes
   * @param elision  separates multiple syllables on a single note
   */
  String text;
  String syllabic;
  boolean isExtended;
  boolean hasElision;
  String[] syllabicTypes = new String[] { "single", "begin", "middle", "end" };

  public Lyric(String text) {
    this.text = text;
  }

  public Lyric(String text, String syllabic) throws IllegalArgumentException {
    if (!Utils.contains(syllabic, syllabicTypes)) {
      throw new IllegalArgumentException("Unknown syllabic type: " + syllabic);
    }
    this.text = text;
    this.syllabic = syllabic;
  }

  public Lyric(String text, String syllabic, boolean hasElision, boolean isExtended)
    throws IllegalArgumentException {
    if (!Utils.contains(syllabic, syllabicTypes)) {
      throw new IllegalArgumentException("Unknown syllabic type: " + syllabic);
    }
    this.text = text;
    this.syllabic = syllabic;
    this.hasElision = hasElision;
    this.isExtended = isExtended;
  }

  public String getText() {
    return this.text;
  }

  public String getSyllabic() {
    return this.syllabic;
  }

  public boolean getElision() {
    return this.hasElision;
  }

  public boolean getExtended() {
    return this.isExtended;
  }
}
