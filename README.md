# AI_jobs_impact

This project generates an interactive treemap visualizing the potential impact of Artificial Intelligence on U.S. occupations based on Bureau of Labor Statistics BLS OEWS data and custom AI impact scores.

## Features

* Visualizes employment numbers as treemap block sizes.
* Colors blocks based on AI impact scores (Red: Negative, White: Neutral, Green: Positive).
* Uses a hierarchical structure (Major, Minor, Broad, Detailed occupations).
* Calculates weighted average AI impact for parent groups.
* Handles OEWS data idiosyncrasies for hierarchy and sums.

## **Requirements/Dependencies:**

Python version: 3.8+
Python libraries:
pandas==2.2.3, plotly==5.24.1, numpy==2.2.4, openpyxl==3.1.5

## **Setup/Installation:**

1. **Clone the repository:**

```bash
git clone https://github.com/jj-squared/AI_jobs_impact.git
cd AI_jobs_impact
```

2. **Create and activate a virtual environment (recommended):**

```bash
python -m venv myvenv  # where myvenv is a directory of your choosing to store the virtual env data. 
# On Windows:
myvenv\Scripts\activate
# 
#On macOS/Linux:
source myvenv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Data Files:**

* national_M2024_dl.xlsx- This is a direct download from https://www.bls.gov/oes/tables.htm and contains occupation codes (OCC_CODE) and number of employed (TOT_EMP) in each occupation. It contains other fields such as average salaries which are not currently used.
* onetsoc_to_AI_impact.xlsx - This file contains a mapping for onetsoc codes in the O*NET database to an AI_impact_score generated using Gemini 2.5 Pro Preview

## **Usage:**

```bash
* python oews_onet_AI_treemap.py
```

This will open a tab in your borwser at 127.0.0.1:xxxx. By clicking on sub-areas you can zoom in and out to see more detail

## **Explanation of AI Impact Scores:**

The initial AI impact scores for detailed occupations are loaded from
onetsoc_to_AI_impact.xlsx. If a detailed occupation is not found, a
default score is applied. Parent group scores are employment-weighted
averages of their children.

The AI impact scores in onetsoc_to_AI_impact.xlsx were generated using Gemini 2.5 Pro prompts against the O*NET database.

* Since Gemini Pro (and presumably other AI models) have already been pretrained on the O*NET DB due to its public nature, it already has a very good understanding of onetsoc codes and the relevant data attached to them

It is highly probable that you will disagree with some of the scores or would like to see a detailed description of why the score is as it is. You can prompt Gemini pro to give a detailed response as to why a particular code has a AI score of x however without precalibration prompts your results may not be normalized against other AI impact scores.

If you would like to create you own set of scores an example prompt is as follows

* **Break into Manageable Batches (Manual Step for You):**
  **Since
  directly uploading a CSV of ~1000 codes and asking for scores on all of
  them in one go might still be too much for a single interactive prompt
  (both for input length and for me to process and output reliably for
  that many), you'll need to break this CSV into smaller chunks.**

**The Gemini Prompt :**

****Initial Setup/System Prompt (once at the beginning of the session):****

I will provide you with lists of O*NET occupation codes and their titles.
Based on your general knowledge of these occupations (informed by O*NET
data), please provide an 'AI Impact Score' for each. The score should
range from -1.0 (largest negative impact/high likelihood of replacement
or significant reduction in demand) to +1.0 (largest positive
impact/strong augmentation leading to increased capability or demand),
with 0.0 being neutral or minimal net impact.**

******Consider factors such as:******

Routineness and predictability of core tasks.

* Cognitive complexity and need for critical thinking, creativity, and novel problem-solving.
* Importance of interpersonal skills, empathy, and complex human interaction.
* Physical demands, especially in varied or unpredictable environments.
* The potential for AI to automate core tasks versus augmenting human capabilities and improving efficiency.

**Output Format:****
For each occupation, provide the O*NET code and the numerical score,
separated by a comma, with each occupation on a new line. For example:**
11-1011.00,0.5
37-3011.00,-0.2

### Example prompt and response for a specific occupation code

#### Prompt:

```I have reviewed some of the scores and would like some details on what went into the assessment. The first is 25-9040```

##### Respsone:

```
You're asking for a breakdown of the score for 25-9042.00 - Teaching Assistants, Preschool, Elementary, Middle, and Secondary School, Except Special Education.

My score for this was -0.1.

You\'re asking for a breakdown of the score for **25-9042.00 - Teaching
Assistants, Preschool, Elementary, Middle, and Secondary School, Except
Special Education**.
My score for this was **-0.1**.

Let\'s break down the reasoning based on the heuristic and my internal
understanding of this O\*NET role:

**Occupation: 25-9042.00 - **Teaching Assistants, Preschool, Elementary,
Middle, and Secondary School, Except Special Education****

**General Role Understanding (from O\*NET knowledge):**
Teaching Assistants (TAs) provide instructional, clerical, and other
support to licensed teachers. They work directly with students,
individually or in small groups, to reinforce lessons, supervise
students in various settings (classroom, lunchroom, playground), help
with grading, prepare materials, and perform administrative tasks.

**Applying the Heuristic Factors:**

1. **Routineness and Predictability of Core Tasks:**

  - **Routine/Predictable Tasks:**

    - Setting up materials for lessons or activities.
    - Distributing and collecting assignments.
    - Basic grading of objective tests or worksheets (e.g.,
      multiple choice, fill-in-the-blank) using an answer key.
    - Supervising students during non-instructional times (e.g.,
      recess, lunch, bus duty) following established rules.
    - Making photocopies, filing, organizing classroom supplies.
    - Assisting with record-keeping (e.g., attendance).
  - **Less Predictable/More Varied Tasks:**

    - Reinforcing lessons with individual students or small
      groups, which requires adapting explanations to student
      needs.
    - Assisting students with learning challenges or who need
      extra help (though complex differentiation is the teacher\'s
      role).
    - Responding to minor behavioral issues or interpersonal
      conflicts between students.
  - *AI Impact Consideration:* Many administrative and some of the
    more routine supervisory/material preparation tasks have
    potential for AI/automation support, or could be streamlined by
    AI tools used by the teacher.
2. **Cognitive Complexity and Need for Critical Thinking, Creativity,
  and Novel Problem-Solving:**

  - **Lower Cognitive Complexity:** The core instructional tasks
    performed by TAs are typically to *reinforce* lessons planned
    and delivered by the lead teacher. They are not usually
    responsible for developing curriculum, designing complex
    assessments, or making high-stakes diagnostic decisions about
    student learning paths.
  - **Adaptability Needed:** They do need to adapt explanations and
    support to individual student questions or difficulties within
    the framework provided by the teacher.
  - *AI Impact Consideration:* AI could provide personalized
    learning tools that offer some of the reinforcement TAs
    currently provide, especially for drill-and-practice or basic
    concept review. However, the in-person adaptation and nuanced
    understanding of a student\'s immediate confusion is still a
    human strength.
3. **Importance of Interpersonal Skills, Empathy, and Complex Human
  Interaction:**

  - **Very High Importance:**

    - Working directly with children/adolescents requires
      patience, empathy, and the ability to build rapport.
    - Providing encouragement and support.
    - Communicating effectively with students, the lead teacher,
      and sometimes parents.
    - Managing small group dynamics.
  - *AI Impact Consideration:* This is a strong area of resistance
    to full AI replacement. While AI can provide interactive
    content, the human element of care, encouragement, and
    understanding individual emotional/social needs is critical.
4. **Physical Demands, Especially in Varied or Unpredictable
  Environments:**

  - **Moderate Physical Demands:** May involve standing for long
    periods, moving around the classroom, assisting younger children
    with physical needs, supervising active play.
  - **Varied Environments:** Classroom, playground, lunchroom, field
    trips.
  - *AI Impact Consideration:* AI itself doesn\'t address these
    directly, but robotics (still far off for this nuanced role)
    would be needed. The variability of the environment and
    interactions makes direct physical replacement by current
    robotics very challenging.
5. **Potential for AI to Automate Core Tasks vs. Augment Human
  Capabilities:**

  - **Automation Potential (leaning towards negative score
    contribution):**

    - Grading of simple assignments.
    - Material preparation (e.g., AI could generate worksheets,
      find resources).
    - Some forms of content delivery or practice (adaptive
      learning software).
    - Administrative tasks (attendance, basic record keeping).
  - **Augmentation Potential (leaning towards positive score
    contribution or mitigating negative):**

    - AI tools could help TAs find tailored resources for students
      they are assisting.
    - AI could help teachers manage classroom logistics more
      efficiently, potentially changing the *types* of support
      tasks TAs do.
    - AI could provide TAs with insights into student progress on
      digital platforms, helping them target support.
  - **Resistant Core Functions:** Direct interpersonal support,
    nuanced behavior management, fostering a positive and supportive
    immediate learning environment for individuals/small groups.

**Score Justification for -0.1 (Slightly Negative / Minimal Net
Impact):**

- **Why not more negative?** The high degree of direct human
 interaction, the need for empathy, and the supervision of children
 in dynamic environments provide significant resistance to full
 automation. The \"care\" aspect is crucial.
- **Why slightly negative?**

 - A number of the TA\'s tasks are administrative or routine
   instructional support (grading simple work, preparing materials,
   basic reinforcement of concepts) that AI-powered educational
   tools or teacher-productivity tools could increasingly absorb or
   make more efficient, potentially reducing the *number* of TA
   hours needed for those specific functions.
 - AI-driven personalized learning platforms could take over some
   of the direct drill-and-practice or content review roles that
   TAs might currently fulfill.
 - The role is generally supportive rather than leading
   instruction, making some of its components more susceptible to
   being \"chipped away\" by technology that assists the lead
   teacher or directly assists students with routine learning.

The **-0.1** reflects a scenario where AI tools might streamline some
tasks or allow teachers to manage larger groups with fewer TAs for
*certain types* of support, or where AI educational software directly
provides some of the reinforcement. However, the need for in-person
support, supervision, and the human element in a classroom setting,
especially with younger children, will likely keep TAs relevant, though
their specific task distribution might evolve. The impact is not seen as
dramatically transformative (either highly positive or highly negative)
but a slight pressure towards efficiency gains that could marginally
reduce demand for the current scope of tasks.

If I were to have access to the detailed task_statements, skills, and
work_activities for TAs, I would look for the proportion of time spent
on easily automatable administrative tasks versus direct, nuanced
student interaction and supervision. If the former is very high, the
score might dip slightly more negative. If the latter is overwhelmingly
dominant, it might move closer to 0.0.
```
