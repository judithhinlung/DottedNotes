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

package org.codeperception.dottednotes.music.format;

public class Font {

  String fontFamily;
  String fontStyle;
  String fontSize;
  String fontWeight;

  public Font() {
    this.fontFamily = null;
    this.fontStyle = null;
    this.fontWeight = null;
    this.fontSize = null;
  }

  public void setFontFamily(String fontFamily) {
    this.fontFamily = fontFamily;
  }

  public void setFontStyle(String fontStyle) {
    this.fontStyle = fontStyle;
  }

  public void setFontWeight(String fontWeight) {
    this.fontWeight = fontWeight;
  }

  public void setFontSize(String fontSize) {
    this.fontSize = fontSize;
  }
}
