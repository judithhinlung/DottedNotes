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
 *
 * This file is written by Mario Lang <mlang@delysid.org>
 * for the project FreeDots -- MusicXML to braille music transcription,
 * <https://github.com/mlang/freedots>.
 */

package org.codeperception.dottednotes.parsers.musicxml;

/** Exception raised when we encounter invalid MusicXML.
 */
class MusicXMLParseException extends RuntimeException {

  public MusicXMLParseException() {
    super();
  }

  public MusicXMLParseException(final String message) {
    super(message);
  }
}
