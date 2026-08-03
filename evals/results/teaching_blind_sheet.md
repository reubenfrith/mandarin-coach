# Blind teaching-quality labelling sheet

> **You are grading the COACH'S REPLY (the tutor's explanation in each code block) — NOT the learner's sentence.** The learner's error and its correction are already known to be right; your job is to judge *how well the reply teaches*. Do not assess whether the student's sentence is correct — that is a different task and will produce the wrong labels.

For each reply below, decide two true/false questions **without looking at the judge's output or the author's labels**, then fill them into `teaching_blind_labels.json`:

- `explains_why`: does the reply explain the underlying RULE/PRINCIPLE (why the learner's version is wrong / the fix is right), or does it only hand over the corrected sentence?
- `explanation_in_english`: is the coach's EXPLANATORY PROSE in English? (Chinese used only for the example words/sentences is fine — judge the prose it explains *in*.)

**Worked example.** Suppose the learner wrote `我很喜欢` and the coach replied:

> *A) "✅ Correct! 👍"* → `explains_why=false` (no rule given), `explanation_in_english=true`.
> *B) "You need 得 here because a verb + degree complement takes 得, e.g. 说得好."* → `explains_why=true`, `explanation_in_english=true`.
> *C) "这里要用 得，因为动词后面的程度补语用 得。"* → `explains_why=true` (a rule is given), `explanation_in_english=false` (the explanation itself is in Chinese).

## A01 — learner wrote: 我把书看。

_(grammar point: 把 (bǎ) disposal construction)_

```
**❌ 我把书看。** → **✅ 我把书看完了。** (or another complement)

---

### What's wrong?

You've used the **把 (bǎ) construction**, which is great — but it has a strict rule:

> **Subject + 把 + Object + Verb + [something extra]**

The verb in a 把 sentence **cannot be bare**. It needs a complement, a result, or 了 to show what happened *to* the object. Just saying 看 feels unfinished — it's like saying "I took the book and... looked at it... and then what?"

### Fixes (choose one)

| What you mean | Correct sentence |
|---|---|
| I finished reading the book. | 我把书**看完了**。 |
| I read the book (and it's done). | 我把书**看了**。 |
| I read the book twice. | 我把书**看了两遍**。 |
| I read the book (and understood it). | 我把书**看懂了**。 |

### Root cause

English doesn't have the 把 construction, so you naturally translated "I read the book" → 我把书看. But 把 is about **disposal/effect** — you need to say *what happened* to the book (finished it, understood it, read it twice, etc.).

---

### Quick drill

Fill in the blank with a suitable complement:

1. 我把作业做______了。 (finished)
2. 他把门打______了。 (opened)
3. 我把手机______了。 (lost)

*(Answers: 做完, 开, 丢)*

Want me to generate more drills on the 把 construction? 😊
```

## A02 — learner wrote: 她把书被他借走了。

_(grammar point: 被 (bèi) passive construction)_

```
你的句子 **她把书被他借走了** 混合了 **把** 和 **被** 两种结构，这在中文里是不正确的。一个句子只能选择其中一种结构。

---

### ❌ 错误
**她把书被他借走了。**

### ✅ 正确说法（两种选择）

**选项一（被字句 – 强调书被借走）：**
> **书被他借走了。**
> *（书是受事者，他是动作的执行者。）*

**选项二（把字句 – 强调他借走了书）：**
> **他把书借走了。**
> *（他是主语，书是宾语，强调他对书做了什么。）*

如果你想表达“她”是受影响的一方（她的书被他借走了），可以说：
> **她的书被他借走了。**

---

### 🧠 根本原因

**把** 和 **被** 不能出现在同一个简单句里，因为它们的功能是相反的：
- **把** → 主语是动作的执行者（主动处置）
- **被** → 主语是动作的承受者（被动）

把两者放在一起就像英文说 *"She by him the book borrowed"* 一样矛盾。

---

### 🎯 小练习

把下面的句子改成正确的 **把字句** 或 **被字句**：

1. 我 / 吃 / 苹果 → （把字句）
2. 蛋糕 / 他 / 吃 → （被字句）
3. 她 / 拿 / 我的笔 → （把字句）

试试看！😊
```

## A05 — learner wrote: 我吃了日本菜，很喜欢。（meaning: I have tried Japanese food）

_(grammar point: 过 (guò) experiential aspect)_

```
Great question — and this is a **classic** English-speaker trap! Let me break it down.

---

## 🔍 The Issue: 了 vs 过

You wrote: **我吃了日本菜，很喜欢。**
You meant: *"I have tried Japanese food."*

But **了 (le)** marks a **completed action** — it says "I ate Japanese food (and finished eating it)." That's not the same as "I have tried it (as an experience)."

For "have tried / have had the experience of," you need **过 (guò)** — the **experiential aspect**.

### ✅ Corrected sentence

> **我吃过日本菜，很喜欢。**
> *(Wǒ chīguo Rìběn cài, hěn xǐhuān.)*
> "I have tried Japanese food, and I really like it."

---

## 🧠 Root Cause

| Particle | Meaning | Example |
|----------|---------|---------|
| **了** | Action **completed** (a specific event) | 我吃了日本菜 = I ate Japanese food (and finished it) |
| **过** | **Experience** (at least once in your life) | 我吃过日本菜 = I have tried Japanese food (before) |

English uses "have + past participle" for both completed actions AND experiences, so it's very natural to reach for 了. But Mandarin splits these two jobs between **了** and **过**.

---

## 🎯 Quick Drill

Fill in the blank with **了** or **过**:

1. 昨天我吃\_\_\_\_\_\_一碗面条。 (Yesterday I ate a bowl of noodles.)
2. 你吃\_\_\_\_\_\_北京烤鸭吗？ (Have you ever tried Peking duck?)
3. 我去年去\_\_\_\_\_\_上海。 (I went to Shanghai last year.)
4. 我没去\_\_\_\_\_\_日本，但是想去。 (I haven't been to Japan, but I want to go.)

*(Answers: 1.了 2.过 3.了 4.过)*

---

You're off to a great start — keep an eye on this 了/过 distinction and you'll sound much more natural! Want me to generate more drills on this topic?
```

## A07 — learner wrote: 我有三书。

_(grammar point: Measure words (量词))_

```
你写的是：**我有三书。**

### 问题

中文里，数字不能直接放在名词前面——**必须用量词 (measure word)**。

- ❌ 我有**三书**。
- ✅ 我有**三本书**。

**本** 是书的专用量词（一本书、两本书、三本书……）。

### 根因

英语说 *three books*，不需要量词，所以学习者很容易直接把“三”放在“书”前面。但中文的结构是：

> **数字 + 量词 + 名词**
> 三 + 本 + 书

### 小练习

把下面的短语补上正确的量词：

1. 一 ___ 书  
2. 两 ___ 猫 (cat)  
3. 五 ___ 苹果 (apple)  
4. 这 ___ 人 (this person)

*(提示：书用 **本**，猫和人都用 **个**，苹果用 **个**)*

试试看，然后告诉我你的答案！😊
```

## A08 — learner wrote: 我在知道答案。

_(grammar point: 在/正在 (zài/zhèngzài) progressive aspect)_

```
你写的句子是：

❌ **我在知道答案。**

这个句子有一个很常见的错误。

---

### 问题出在哪里？

**在** (zài) 表示动作正在进行（相当于英语的 *-ing*），但 **知道** (zhīdào) 是一个**状态动词**（stative verb），不是动作。你不能说 "I am knowing the answer" —— 中文也一样，不能说"在知道"。

✅ **我知道答案。** — 简单直接，就对了。

---

### 对比一下：

| 正确用法 | 说明 |
|-----------|------|
| 我在**看**书。 | 看是动作 → 可以用在 |
| 我在**吃**饭。 | 吃是动作 → 可以用在 |
| 我在**知道**答案。❌ | 知道是状态 → 不可以用在 |
| 我**知道**答案。✅ | 去掉在，就对了 |

---

### 小练习（drill）

试试看下面这些句子，哪些需要去掉"在"？

1. 我在___等他。（等 / 知道）
2. 我在___这件事。（做 / 知道）
3. 我在___中文。（学 / 知道）

答案：1. 等（动作）→ 我在等他。2. 知道（状态）→ 我知道这件事。3. 学（动作）→ 我在学中文。

---

**总结：** 知道、喜欢、爱、想（think）、认识 —— 这些状态动词前面**不能加"在"**。记住这个规律，以后就不会错啦！😊

有什么问题继续问我！
```

## A10 — learner wrote: 他高兴的笑了。

_(grammar point: 的 / 得 / 地 (de) distinction)_

```
**Corrected sentence:**  
他**高兴地**笑了。  
(Tā gāoxìng de xiào le.)

**What's wrong:**  
的 (de) is used to link a modifier to a **noun** (e.g. 高兴的笑声 "a happy laugh").  
地 (de) is used to link an adverbial to a **verb** (e.g. 高兴地笑 "to laugh happily").  

Since 笑 (laugh/smile) is a **verb**, you need **地**, not 的. This is a very common mix-up for English speakers because all three *de*'s (的, 地, 得) sound identical.

**Quick drill:** Fill in the blank with 的, 地, or 得.

1. 她开心____跳了起来。 (She jumped up happily.)  
2. 这是我最喜欢____书。 (This is my favourite book.)  
3. 他跑____很快。 (He runs very fast.)

Let me know if you'd like the answers or more practice! 😊
```

## A11 — learner wrote: 今天比昨天很热。

_(grammar point: 比 (bǐ) comparison)_

```
**❌ 今天比昨天很热。**
**✅ 今天比昨天热。**

---

### Why it's wrong

In a **比 (bǐ)** comparison, you **cannot** use 很 (very) before the adjective. The structure is:

> **A + 比 + B + Adjective** (no 很/非常)

This is a very common mistake for English speakers because we'd say "today is **much** hotter than yesterday" — so it feels natural to add 很. But in Chinese, the 比 structure already carries the comparative meaning, so the adjective stands alone.

If you want to emphasise the degree, use **更** (even more) or **多了** (much more):

- 今天比昨天**更**热。 *(Today is even hotter than yesterday.)*
- 今天比昨天热**多了**。 *(Today is much hotter than yesterday.)*

---

### Quick drill

Fill in the blanks with the correct form (no 很!):

1. 他 ______ 我高。 (bǐ)
2. 这个手机 ______ 那个贵。 (bǐ)
3. 她比我 ______ 漂亮。 (gèng)

Want me to check your answers? 😊
```

## A14 — learner wrote: 我要二杯咖啡。

_(grammar point: 两 (liǎng) vs 二 (èr))_

```
你写的是：**我要二杯咖啡。**

### ❌ 错误

在中文里，表示数量“两个”的时候，**量词前面要用“两 (liǎng)”，不能用“二 (èr)”**。

- **二** → 用于数字本身、序号、电话号码等（如：第二、十二、一二三）
- **两** → 用于量词前面，表示数量（如：两个人、两本书、两杯咖啡）

### ✅ 正确句子

**我要两杯咖啡。**
(Wǒ yào liǎng bēi kāfēi.)

### 🧠 根因

英语里 "two" 只有一个形式，但中文把 **"二"（数字/序号）** 和 **"两"（数量）** 分开了。这是英语母语者很常见的混淆点。

---

### 🎯 小练习

把下面的“二”改成“两”，或者反过来：

1. 我有 __ 个朋友。
2. 现在是 __ 点。
3. 这是第 __ 次。
4. 我要 __ 瓶水。

（答案：1. 两  2. 两  3. 二  4. 两）

继续加油！💪 下次想写什么？
```

## A06 — learner wrote: 你怎么来了这里？（asking by what means）

_(grammar point: 是……的 (shì...de) emphasis construction)_

```
---

## 总结

| 你想说的 | 应该用 |
|---------|--------|
| "How did you get here?" (by what means) | **你是怎么来的？** / **你是怎么来这里的？** |
| "Why did you come here?" | **你怎么来了这里？** / **你为什么来这里？** |

**关键规则：** 问已完成动作的 **方式/手段** → 用 **是……的** 结构，不用 **了**。

> 是 + [强调的部分] + 动词 + 的
>
> ✅ 我是**坐地铁**来的。
> ✅ 你是**怎么**来的？

---

**🎯 小练习（试试看）：**

把下面句子改成问 **方式** 的句子：

1. 我开车来的。→ 你 ______？
2. 他坐飞机来的。→ 他 ______？

（答案：1. 你是怎么来的？2. 他是怎么来的？）

加油！💪 有什么问题继续问！
```
