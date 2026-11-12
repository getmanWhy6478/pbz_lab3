
GET_STUDENTS = """
MATCH (s:Student)
RETURN s.studentId AS id, s.name AS name, s.goal AS goal
ORDER BY s.name
"""

GET_STUDENT_PROFILE = """
MATCH (s:Student {studentId: $student_id})
MATCH (s)-[:COMPLETED]->(c:Course)-[:TEACHES]->(sk:Skill)
RETURN s.name AS name, s.goal AS goal,
       collect(DISTINCT c.title) AS courses,
       collect(DISTINCT sk.name) AS skills
"""

GET_GAP_ANALYSIS = """
MATCH (s:Student {studentId: $student_id})-[:TARGETS]->(j:Job)
MATCH (j)-[r:REQUIRES]->(sk:Skill)
WHERE NOT (s)-[:COMPLETED]->(:Course)-[:TEACHES]->(sk)
RETURN sk.name AS skill, r.priority AS priority
ORDER BY CASE r.priority WHEN 'must' THEN 1 ELSE 2 END
"""

GET_LEARNING_PATH = """
MATCH (s:Student {studentId: $student_id})-[:TARGETS]->(j:Job)
MATCH (j)-[:REQUIRES {priority: 'must'}]->(missing:Skill)
WHERE NOT (s)-[:COMPLETED]->(:Course)-[:TEACHES]->(missing)
MATCH neededPath = (prereq:Course)-[:PREREQUISITE*0..3]->(target:Course)-[:TEACHES]->(missing)
WHERE NOT (s)-[:COMPLETED]->(prereq)
WITH missing, [c IN nodes(neededPath) WHERE c:Course] AS courses
RETURN 
    missing.name AS skill,
    [c IN courses | c.title] AS path,
    reduce(total = 0, c IN courses | total + c.durationHours) AS hours,
    reduce(total = 0, c IN courses | total + c.price) AS price
ORDER BY hours ASC
"""

GET_MENTORS = """
MATCH (s:Student {studentId: $student_id})-[:TARGETS]->(j:Job)-[:AT]->(c:Company)
MATCH (m:Mentor)-[:WORKS_AT]->(c)
MATCH (j)-[:REQUIRES]->(missing:Skill)<-[:HAS_SKILL]-(m)
WHERE NOT (s)-[:COMPLETED]->(:Course)-[:TEACHES]->(missing)
WITH m, c.name AS company, collect(DISTINCT missing.name) AS skills, count(missing) AS matches
WHERE matches >= 1
RETURN m.name AS mentor, m.experienceYears AS experience, 
       m.hourlyRate AS rate, company, skills, matches
ORDER BY matches DESC, m.experienceYears DESC
"""

GET_PEERS = """
MATCH (me:Student {studentId: $student_id})-[:TARGETS]->(j:Job)-[:AT]->(c:Company)
MATCH (peer:Student)-[:TARGETS]->(:Job)-[:AT]->(c)
WHERE peer <> me
MATCH (me)-[:COMPLETED]->(:Course)-[:TEACHES]->(common:Skill)<-[:TEACHES]-(:Course)<-[:COMPLETED]-(peer)
WITH peer, collect(DISTINCT common.name) AS skills
WHERE size(skills) >= 1
RETURN peer.name AS peer, peer.goal AS goal, skills
ORDER BY size(skills) DESC
"""

GET_MARKET_STATS = """
MATCH (j:Job)-[r:REQUIRES]->(sk:Skill)
RETURN sk.name AS skill, 
       count(j) AS jobs,
       sum(CASE WHEN r.priority = 'must' THEN 1 ELSE 0 END) AS must,
       sum(CASE WHEN r.priority = 'nice' THEN 1 ELSE 0 END) AS nice
ORDER BY jobs DESC
LIMIT 10
"""