'''
    talks to sql db using halt
'''

import halt

class CreateWorkBookError(Exception): pass
class NoHotkeyError(CreateWorkBookError): pass
class UniqueNameError(CreateWorkBookError): pass
class UniqueHotkeyError(CreateWorkBookError): pass


def book_create(db, book, profile, hotkey=None, **kwargs):
    '''
    For creating a new workbook, NOT updating one

    use this with the exceptions
    NoHotkeyError
    UniqueNameError
    UniqueHotkeyError

    On no hotkey the book will still be created

    No changes to db on the other errors

    on success returns the  keycode and masks
    '''
    cond = "where Name = 'System Default'"
    options = halt.load_column(db, 'DefaultOptions', ('MashConfig',), cond)
    options = halt.objectify(options)

    for k, v in kwargs.items():
        if k not in options:
            raise KeyError(k + 'not recognized, add a default first to dbcreate.py')
        else:
            options[k] = v
    try:
        # i am doing 2 seperate queries that depend on each other
        # the cur is only commited at the end so i dont have to undo anythin on
        # a fail
        con = halt.insert(db, 'Books', options, mash=True, commit=False)
        if hotkey:
            assert type(hotkey) != str
            _add_hotkey(hotkey, profile, bookname, con)
            con.commit()
        else:
            raise NoHotkeyError
    except sqlite3.IntegrityError as err:
        raise UniqueNameError('Name for that widget already exists!')
    finally:
        with suppress(UnboundLocalError):
            con.close()


def _add_hotkey(full_hotkey, profile, bookname, con=None):
    hk_options = {'Hotkey': full_hotkey, 'Profile': profile, 'Bookname': bookname}
    try:
        halt.insert(db, 'Hotkeys', hk_options, con=con)
    except sqlite3.IntegrityError as err:
        raise UniqueHotkeyError(str(err))


def book_delete(db, book):
    # Close any open windows # TODO
    # for note in note_references.values():
    # if note.page.Bookname == bookname:
    # note.toplevel.destroy()
    cond = "where Name == '{0}' and Profile == '{1}'"\
                    .format(bookname, profile)
    halt.delete('db', 'Books', cond)

    cond = "where Bookname == '{0}' and Profile =='{1}'"\
                    .format(bookname, profile)
    halt.delete(db, 'Hotkeys', cond)
    halt.delete(db, 'Pages', cond)
    # Remember to Update values that other colums depend on first

def book_get_all(db):
    results = dbtools.load_column(db, 'Books', 'Name')
    return [x[0] for x in results]


def hotkey_get_all(db, profile):
    '''returns a list of all hotkeys for a given profile'''
    hotkeys = []
    cond = "where Profile == '" + profile + "'"
    for hk in  halt.load_column(db, 'Hotkeys', ('Hotkey',), cond):
        hotkeys.append(halt.objectify(hk))
    return hotkeys


def _page_save(profile, book, program, specific):
    assert type(program) in (list, tuple)
    to_save = {
        'Profile': profile,
        'Bookname': book,
        'Program': program,
        'Symlink': None,
        'SpecificName': specific,
    }

    if specific is None:
        specific = ''
    if program is None:
        program = ''

    name = book + program[0] + profile + specific # TODO improve this
    cond = "where Name == '{0}'".format(name)
    return to_save, cond


def page_create(db, profile, book, program, specific):
    to_save, cond = _page_save(profile, book, program, specific)
    halt.insert(db, 'Pages', to_save, mash=False, commit=True)


def page_update(db, profile, book, program, specific):
    to_save, cond = _page_save(profile, book, program, specific)
    halt.update(db, 'Pages', to_save, mash=False, commit=True)


def page_get_all(db, address=True):
    '''
    return eith as address
    or profile book, program, program, specific
    '''
    columns = ('Bookname', 'Program', 'Profile', 'SpecificName')
    results = halt.load_column(db, 'Pages', columns)
    if address:
        for row in results:
            Bookname, Program, Profile, SpecificName = row
            yield make_page_address(
                    Profile, Bookname, Program, SpecificName)
    else:
        for row in results:
            Bookname, Program, Profile, SpecificName = row
            yield Profile, Bookname, Program, SpecificName


def profile_create(db, name):
    '''
    saves a new profile entry in the database
    '''
    try:
        halt.insert(db, 'Profiles', {"name": name})
    except halt.HaltException:
        return False
    else:
        return True


def profile_delete(db, profile):
    if profile not in profile_get_all(db):
        return False
    cond = "where Name == '{0}'".format(profile)
    halt.delete(db, 'Profiles', cond)
    return True


def profile_set_active(db, profile):
    '''Sets the given profile as being active'''
    # Remove the previous active
    cond = "where Active == 1"
    halt.update(db, 'Profiles', {'Active': False}, cond)

    # Update the new
    cond = "where Name == '{0}'".format(profile)
    halt.update(db, 'Profiles', {'Active': True},  cond)


def profile_get_active(db):
    '''Returns the currently active profile'''
    cond = "where Active == 1"
    results = halt.load_column(db, 'Profiles', ('Name',), cond)
    profile = results[0][0]
    return profile


def profile_get_all(db):
    ''' Returns a list of profiles on the system '''
    results = halt.load_column(db, 'Profiles', ('Name',))
    return [x[0] for x in results]

