"""No biological records: test complete case-only recurrence accounting."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from macaronesia_s1_recurrence_v1_266 import recurrence_report, normalize_name


def row(name='Alpha alba',island='I1',arch='A',year='1900',status='Extirpation (Island level)',certainty='Well-supported',habit='woody'):
    return {'Species':name,'Island':island,'Archipelago':arch,'Date':year,
            'Extinction category':status,'Category':certainty,'Habit':habit,
            'Pollination mechanism':'entomophily','Seed dispersal mechanism':'anemochory','Endemicity':'single-archipelago endemic'}


def fixture():
    return [row(),row(name='Alpha alba1',island='I2',year='1950'),
            row(name='Beta beta'),row(name='Beta beta',island='I2',year='2000'),
            row(name='Gamma gamma',island='I3',arch='B',year='1960'),
            row(name='Gamma gamma',island='I3',arch='B',year='1960'),
            row(name='Global gone',status='Globally extinct'),
            row(name='Old old',certainty='Pre-Linnean'),
            row(name='Doubtful dud',certainty='Doubtful')]


def test_raw_vs_annotation_name_sensitivity_and_deduplication():
    r=recurrence_report(fixture())
    a,b=r['raw_names'],r['numeric_annotation_sensitivity']
    assert (a['raw_strict_rows'],a['taxon_island_pairs'],a['distinct_taxa'])==(6,5,4)
    assert (b['taxon_island_pairs'],b['distinct_taxa'],b['repeat_taxa'])==(5,3,2)
    assert a['duplicate_pair_records']==b['duplicate_pair_records']==1
    assert b['taxa_by_number_of_islands']=={'1':1,'2':2}
    assert r['all_S1_raw_distinct_taxon_strings']==7
    assert r['all_S1_annotation_normalized_distinct_taxa']==6
    assert 'Alpha' not in str(r) and 'Beta' not in str(r)


def test_dates_are_last_record_gaps_not_extinction_intervals():
    r=recurrence_report(fixture())['numeric_annotation_sensitivity']
    assert r['last_record_gaps_years']['exact_two_island_taxa']==2
    assert r['last_record_gaps_years']['parseable_pairs']==2
    assert r['last_record_gaps_years']['median']==75
    assert r['last_record_gaps_years']['sorted_gaps']==[50,100]
    assert r['archipelagos']['A']['taxon_island_pairs']==4
    assert r['archipelagos']['B']['taxon_island_pairs']==1
    assert r['cross_archipelago_repeat_taxa']==0


def test_conflicting_duplicate_years_not_arbitrarily_selected():
    x=[row(),row(year='1910'),row(island='I2',year='1950')]
    r=recurrence_report(x)['raw_names']
    assert r['conflicting_pair_dates']==1
    assert r['last_record_gaps_years']['parseable_pairs']==0


def test_source_annotations_do_not_silently_change_primary_taxa():
    assert normalize_name('Alpha  alba¹',strip_annotations=True)=='alpha alba'
    assert normalize_name('Alpha  alba1',strip_annotations=False)=='alpha alba1'
    r=recurrence_report([row(),row(name='Alpha alba1')])
    assert r['raw_names']['taxon_island_pairs']==2
    assert r['numeric_annotation_sensitivity']['taxon_island_pairs']==1
    assert r['raw_names']['confidence_by_status']['Extirpation (Island level)']['Well-supported']==2


def test_all_invalid_non_species_rows_rejected():
    try:
        recurrence_report([{'Species':''}])
    except ValueError:
        pass
    else:
        assert False,'Required source schema must be checked'
