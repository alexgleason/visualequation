#!/usr/bin/env python2
"""This is the file to execute the program."""
import sys
import tempfile
import shutil
import os

import pygame
from pygame.locals import *

import dirs
import symbols
import maineq
import conversions
import menu

def draw_screen(screen, editingeq, mainmenu):
    """ Draw equation, menuitems and symbols."""
    screen.fill((255, 255, 255))
    screen.blit(editingeq.image, editingeq.rect)
    for menuitem in mainmenu.menuitems:
        screen.blit(menuitem.image, menuitem.rect)
    mainmenu.active_symbs.draw(screen)
    pygame.display.flip()

def main(*args):
    """ This the main function of the program."""
    version = '0.1.3'
    # Prepare a temporal directory to manage all intermediate files
    temp_dirpath = tempfile.mkdtemp()
    # Prepare pygame
    screen_w = 800
    screen_h = 600
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((screen_w, screen_h), RESIZABLE)
    pygame.display.set_caption("Visual Equation")

    # Prepare the equation to edit which will be showed by default
    init_eq = [symbols.NEWARG]
    screen_center = (screen_w//2, screen_h//2)
    editingeq = maineq.EditableEqSprite(init_eq, screen_center,
                                            temp_dirpath)
    # Create the menu
    mainmenu = menu.Menu(screen_w, screen_h, temp_dirpath)
    # Pygame loop
    ongoing = True
    while ongoing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ongoing = False
            elif event.type == VIDEORESIZE:
                screen = pygame.display.set_mode(event.size, RESIZABLE)
                screen_center = (event.w//2, event.h//2)
                editingeq.set_center(event.w//2, event.h//2)
                mainmenu.set_screen_size(event.w, event.h)
            elif event.type == MOUSEBUTTONDOWN:
                for index, menuitem in enumerate(mainmenu.menuitems):
                    if menuitem.mousepointed():
                        mainmenu.select_item(index)
                for symb in mainmenu.active_symbs:
                    if symb.mousepointed():
                        if pygame.key.get_mods() & KMOD_SHIFT:
                            editingeq.insert_substituting(symb.code)
                        else:
                            editingeq.insert(symb.code)
                if editingeq.mousepointed():
                    editingeq.next_sel()
            elif event.type == KEYDOWN:
                try:
                    code = ord(event.unicode)
                    # If it belongs to 0-9 or A-Z or a-z
                    if 48 <= code <= 57 or 65 <= code <= 90 \
                       or 97 <= code <= 122:
                        editingeq.insert(event.unicode)
                except TypeError:
                    pass
                if event.unicode == '\\':
                    editingeq.insert(r'\backslash')
                elif event.unicode == '~':
                    editingeq.insert(r'\sim')
                elif event.unicode == '|':
                    editingeq.insert(r'|')
                elif event.unicode == '!':
                    editingeq.insert('!')
                elif event.unicode == '$':
                    editingeq.insert(r'\$')
                elif event.unicode == '%':
                    editingeq.insert(r'\%')
                elif event.unicode == '&':
                    editingeq.insert(r'\&')
                elif event.unicode == '/':
                    editingeq.insert('/')
                elif event.unicode == ')':
                    editingeq.insert(')')
                elif event.unicode == '(':
                    editingeq.insert('(')
                elif event.unicode == '=':
                    editingeq.insert('=')
                elif event.unicode == '?':
                    editingeq.insert('?')
                elif event.unicode == "'":
                    editingeq.insert("'")
                elif event.unicode == '@':
                    editingeq.insert('@')
                elif event.unicode == '#':
                    editingeq.insert(r'\# ')
                elif event.unicode == '[':
                    editingeq.insert('[')
                elif event.unicode == ']':
                    editingeq.insert(']')
                elif event.unicode == '{':
                    editingeq.insert(r'\{')
                elif event.unicode == '}':
                    editingeq.insert(r'\}')
                elif event.unicode == '*':
                    editingeq.insert('*')
                elif event.unicode == '+':
                    editingeq.insert('+')
                elif event.unicode == '-':
                    editingeq.insert('-')
                elif event.unicode == '_':
                    editingeq.insert_substituting(symbols.SUBINDEX)
                elif event.unicode == '^':
                    editingeq.insert_substituting(symbols.SUPERINDEX)
                elif event.unicode == '<':
                    editingeq.insert('<')
                elif event.unicode == '>':
                    editingeq.insert('>')
                elif event.unicode == ',':
                    editingeq.insert(',')
                elif event.unicode == '.':
                    editingeq.insert('.')
                elif event.unicode == ';':
                    editingeq.insert(';')
                elif event.unicode == ':':
                    editingeq.insert(':')
                    # First cases with mods, this avoids false positives
                    # CONTROL + letter
                elif event.key == K_z and pygame.key.get_mods() & KMOD_CTRL:
                    editingeq.recover_prev_eq()
                elif event.key == K_y and pygame.key.get_mods() & KMOD_CTRL:
                    editingeq.recover_next_eq()
                elif event.key == K_s and pygame.key.get_mods() & KMOD_CTRL:
                    editingeq.save_eq()
                elif event.key == K_c and pygame.key.get_mods() & KMOD_CTRL:
                    editingeq.sel2eqbuffer()
                elif event.key == K_x and pygame.key.get_mods() & KMOD_CTRL:
                    editingeq.sel2eqbuffer()
                    editingeq.remove_sel()
                elif event.key == K_v and pygame.key.get_mods() & KMOD_CTRL:
                    editingeq.eqbuffer2sel()
                elif event.key == K_p and pygame.key.get_mods() & KMOD_CTRL:
                    editingeq.left_NEWARG()
                elif event.key == K_o and pygame.key.get_mods() & KMOD_CTRL:
                    neweq = conversions.open_eq()
                    if neweq is not None:
                        editingeq = maineq.EditableEqSprite(neweq,
                                                            screen_center,
                                                            temp_dirpath)
                    # Cases without mods
                elif event.key == K_RIGHT:
                    editingeq.next_sel()
                elif event.key == K_LEFT:
                    editingeq.previous_sel()
                elif event.key == K_UP:
                    mainmenu.next_item()
                elif event.key == K_DOWN:
                    mainmenu.prev_item()
                elif event.key == K_SPACE:
                    editingeq.insert(r'\,')
                elif event.key == K_TAB:
                    editingeq.next_sel()
                elif event.key == K_BACKSPACE or event.key == K_DELETE:
                    editingeq.remove_sel()

        draw_screen(screen, editingeq, mainmenu)
        clock.tick(30)

    # Delete the temporary directory and files before exit
    shutil.rmtree(temp_dirpath)
    sys.exit(0)

if __name__ == '__main__':
    main(*sys.argv[1:])
