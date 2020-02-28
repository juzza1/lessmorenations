from collections import defaultdict
import os
import re
import sys


class X2Str(str):
    pass


def ordered_replace(mapping, old_key, new_key, new_val):
    after = {}
    for k in list(mapping.keys()):
        if k == old_key:
            after[new_key] = new_val
            del mapping[k]
        elif after:
            after[k] = mapping[k]
            del mapping[k]
    for a in after:
        mapping[a] = after[a]


def cline(settings):
    keyvals = []
    for s in settings:
        keyval = '{}='.format(s)
        if isinstance(settings[s], X2Str):
            keyval += '"{}"'.format(settings[s])
        else:
            keyval += settings[s]
        keyvals.append(keyval)
    line = '+BodyPartTemplateConfig=({})'.format(', '.join(keyvals))
    return line


def part(part_settings, soldier_class):
    out = []
    seen = set()
    for s in part_settings:
        if s['ArchetypeName'] in seen:
            continue
        s['CharacterTemplate'] = X2Str('{}Soldier'.format(soldier_class))
        old_template = s['TemplateName']
        if s['PartType'] == 'Torso':
            for atype in ['{}Armor', 'Plated{}Armor', 'Powered{}Armor']:
                s['ArmorTemplate'] = X2Str(atype.format(soldier_class))
                s['TemplateName'] = X2Str(old_template + '_{}'.format(atype.format(soldier_class)))
                out.append(cline(s))
        else:
            ordered_replace(s, 'ArmorTemplate', 'bAnyArmor', 'true')
            s['TemplateName'] = X2Str(old_template + '_{}'.format(soldier_class))
            out.append(cline(s))
        seen.add(s['ArchetypeName'])
    return out


def main():
    all_settings = defaultdict(list)
    with open(sys.argv[1]) as f:
        for line in f.read().splitlines():
            if line.startswith(';') or not line:
                continue
            if not line.startswith('+BodyPartTemplateConfig='):
                if line.startswith('[XComGame.X2BodyPartTemplateManager]'):
                    continue
                else:
                    print('Unknown line: {}'.format(line))
                    sys.exit()
            pairs = (p.strip() for p in re.match(r'\+BodyPartTemplateConfig=\((.*)\)', line).group(1).split(','))
            settings = {}
            for p in pairs:
                k, v = p.split('=')
                if re.fullmatch(r'".*"', v):
                    v = X2Str(v.strip('"'))
                settings[k] = v
            if settings['PartType'] in {'FacePropsUpper', 'Hair', 'Helmets'}:
                continue
            if settings['PartType'] not in {'Torso', 'Legs', 'Arms', 'LeftArm', 'RightArm', 'TorsoDeco', 'LeftArmDeco', 'RightArmDeco'}:
                print('Unknown bodytype: {}'.format(settings['PartType']))
                sys.exit()
            all_settings[settings['PartType']].append(settings)

    heroes = {'1': 'Reaper', '2': 'Skirmisher', '3': 'Templar'}
    c = input('Hero type:\n{}\n'.format('\n'.join('{}: {}'.format(k, v) for k, v in sorted(heroes.items()))))
    hero = heroes[c]
    backup = '{}_old{}'.format(*(c for c in os.path.splitext(sys.argv[1])))
    os.replace(sys.argv[1], backup)
    with open(sys.argv[1], 'w') as f:
        f.write('[XComGame.X2BodyPartTemplateManager]')
        f.write('\n\n; {} Torso\n'.format(hero))
        f.write('\n'.join(part(all_settings['Torso'], hero)))
        for s in all_settings:
            if s != 'Torso':
                f.write('\n\n; {} {}\n'.format(hero, s))
                f.write('\n'.join(part(all_settings[s], hero)))


if __name__ == '__main__':
    main()