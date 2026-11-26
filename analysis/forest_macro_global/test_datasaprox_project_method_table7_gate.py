"""JATS Table 7 and source-design crosswalk tests: pure metadata only."""
import sys,pytest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import datasaprox_project_method_table7_gate as d

def sample_jats(scope="complete"):
    return f'''<article><front><article-meta>
    <article-id pub-id-type="doi">10.3897/BDJ.14.e187021</article-id>
    </article-meta></front><body>
    <table-wrap><label>Table 6.</label><table><tbody>
    <tr><td>OTHER</td><td>not a project</td></tr>
    </tbody></table></table-wrap>
    <table-wrap><label>Table 7.</label><caption><p>Project completeness</p></caption>
    <table><thead><tr><th>Owner</th><th>Project</th><th>Dominant</th>
    <th>Families</th><th>Taxa</th><th>Community</th></tr></thead>
    <tbody>
    <tr><td>P1</td><td>Project Á</td><td>Elateridae 28%</td><td>18</td><td>8</td><td>{scope}</td></tr>
    <tr><td>P2</td><td>Project B</td><td>Cerambycidae 57%</td><td>7</td><td>3</td><td>partial</td></tr>
    <tr><td>P3</td><td>Project C</td><td>Curculionidae 20%</td><td>40</td><td>11</td><td>complete</td></tr>
    </tbody></table></table-wrap></body></article>'''.encode("utf-8")

def test_paper_table7_exact_doi_and_completeness_and_unicode():
    p=d.paper_table7(sample_jats())
    assert len(p)==3
    assert p[(d.norm("P1"),d.norm("Project A\u0301"))]["published_project_community_scope"]=="complete"
    assert p[(d.norm("P2"),d.norm("Project B"))]["published_project_median_taxa_per_sample"]==3
    assert p[(d.norm("P2"),d.norm("Project B"))]["published_project_family_count"]==7
    assert "OTHER" not in str(p)

def test_reject_unrelated_article_table_identity():
    with pytest.raises(ValueError,match="DOI_IDENTITY"):
        d.paper_table7(sample_jats().replace(b"e187021",b"e999999"))

def make_source_candidates():
    # 24 plots×1, 20 plots×3 (62 total), 1 plot×1 = 87 pairs, 45 plots.
    events={}
    i=0
    for producer,project,nplot,nperiod in (
        ("P1","Project A\u0301",24,24),
        ("P2","Project B",20,62),
        ("P3","Project C",1,1)
    ):
        for k in range(nperiod):
            plot="plot_"+str(k%nplot)
            period="2024-"+str(k//nplot+1).zfill(2)
            for stratum in ("upper","lower"):
                i+=1
                cond="treatment_high" if stratum=="upper" else "treatment_low"
                events[(producer,project,"evt"+str(i))]=(
                  stratum,plot,"polytrap","crossed","", # overwritten below
                  "no-bait","clear",period,14,
                )
                v=list(events[producer,project,"evt"+str(i)])
                v[4]=cond
                events[producer,project,"evt"+str(i)]=tuple(v)
    return events

def test_source_project_ladder_matches_article_not_a_biological_height_effect():
    src=make_source_candidates()
    publication=d.paper_table7(sample_jats())
    result=d.crosswalk(src,set(),publication)
    assert result["candidate_without_ID_condition_paired_units"]==87
    assert result["candidate_without_ID_condition_distinct_plot_keys"]==45
    assert result["candidate_projects_matched_to_published_Table7"]==3
    assert result["candidate_projects_published_complete"]==2
    assert result["candidate_projects_published_partial"]==1
    assert [v["original_matched_plot_count"] for v in result["candidate_project_metadata"]]==[24,20,1]
    assert [v["paired_plot_period_method_units_nonindependent"] for v in result["candidate_project_metadata"]]==[24,62,1]
    assert all(v["upper_lower_shared_ID_condition_nonempty_code_count"]==0
               for v in result["candidate_project_metadata"])
    assert all(v["source_declared_upper_treatment_codes_public_metadata_only"]==["treatment_high"]
               for v in result["candidate_project_metadata"])
    assert all(v["source_declared_lower_treatment_codes_public_metadata_only"]==["treatment_low"]
               for v in result["candidate_project_metadata"])
    assert result["public_source_treatment_codes_never_suffice_to_infer_causal_height_effect"]
    assert result["original_same_treatment_design_scientific_STOP_preserved"]
    assert result["no_taxon_species_abundance_geo_or_raw_field_ID_access"]
    assert result["no_biological_community_composition_result"]
    assert result["candidate_project_metadata"][1]["journal_published_project_title_publication_only"]=="Project B"
    assert result["candidate_project_metadata"][1]["journal_published_provider_code_publication_only"]=="P2"
    assert result["published_only_author_provided_public_project_titles_not_site_event_ids"]
    assert "plot_0" not in str(result)
    assert "evt1" not in str(result)

def test_missing_table7_match_is_not_assumed_complete():
    src=make_source_candidates()
    table=d.paper_table7(sample_jats())
    table.pop((d.norm("P2"),d.norm("Project B")))
    res=d.crosswalk(src,set(),table)
    assert res["candidate_projects_matched_to_published_Table7"]==2
    assert res["candidate_project_metadata"][1]["journal_published_Table7_scope"]=="NOT_VERIFIED"
    assert not res["candidate_project_metadata"][1]["journal_published_Table7_exact_source_project_match"]

def test_published_jats_producer_rowspan_and_blank_cell_inherit_author_code():
    raw=sample_jats()
    insert=b'<tr><td></td><td>Second project A</td><td>Elateridae 12%</td><td>21</td><td>10</td><td>complete</td></tr>'
    target=b'<tr><td>P2</td><td>Project B</td>'
    assert target in raw
    amended=raw.replace(target,insert+target)
    table=d.paper_table7(amended)
    assert table[("p1","second project a")]["published_project_community_scope"]=="complete"
    # Source table with physical rowspan may omit first <td> entirely.
    five=b'<tr><td>Third project A</td><td>Elateridae 15%</td><td>22</td><td>11</td><td>complete</td></tr>'
    table2=d.paper_table7(amended.replace(target,five+target))
    assert table2[("p1","third project a")]["published_project_family_count"]==22

def test_identical_duplicate_and_conflicting_author_table7_project_quarantine():
    base=sample_jats()
    target=b'<tr><td>P2</td><td>Project B</td>'
    assert target in base
    same=b'<tr><td>P1</td><td>Project \xc3\x81</td><td>Elateridae 28%</td><td>18</td><td>8</td><td>complete</td></tr>'
    doubled=base.replace(target,same+target)
    table,audit=d.paper_table7(doubled,return_audit=True)
    assert audit["source_article_table7_identical_duplicate_rows"]==1
    assert table[("p1",d.norm("Project Á"))]["published_project_family_count"]==18
    conflict=b'<tr><td>P1</td><td>Project \xc3\x81</td><td>Elateridae 28%</td><td>18</td><td>8</td><td>partial</td></tr>'
    conflicted=base.replace(target,conflict+target)
    table2,audit2=d.paper_table7(conflicted,return_audit=True)
    assert audit2["source_article_table7_conflicting_project_keys_excluded"]==1
    assert ("p1",d.norm("Project Á")) not in table2
