# Before the Rain Stops

Original tool example. The setup note before the entry does not appear to the player; this scene needs neither a mystery nor a grand theme.

::scene START
## An Umbrella Turned Inside Out

[CUE: Keep the sound of rain under the eaves; without audio, preserve the readable view of rain below.]

Xu Ning set the dripping umbrella in the bucket.

**A-He:** It dumped water on me again today.

**Xu Ning:** Maybe put the side with the hole on the bottom.

**A-He:** That side is my head.

The umbrella in the bucket slowly turned inside out. Xu Ning held out her intact umbrella, then glanced at the ribs A-He was still gripping.

::choice OFFER
::option lend | Lend her your umbrella; she can return it tomorrow.
::set borrowed = true
**A-He:** I'll give it back tomorrow.

**Xu Ning:** Then let's hope it doesn't rain tomorrow too.
::goto RETURN
::option repair | Let's look at that bent rib together.
::set repaired = true
**A-He:** Give it a chance to explain itself.

**Xu Ning:** All right. You can speak for it.
::goto REPAIR
::endchoice

::scene REPAIR
## Under the Eaves

A-He held the rib steady while Xu Ning tried to move the clasp. The canopy sprang open. They both flinched backward, neither letting go first.

**Xu Ning:** That was a forceful explanation.

She took a note from her pocket and wedged it under the clasp. A-He saw what it said: “Friday: remember to pick up the book.”

::choice NOTE
::option ask | Ask what the book is.
::set knows_book = true
**Xu Ning:** Gardening. My cactus has started to feel sorry for me.

**A-He:** Did it tell you that?

**Xu Ning:** It leaned over toward the next balcony.
::option wait | Hold the other umbrella rib steady for her.
**A-He:** This side is set.

**Xu Ning:** Don't let go. Let me enjoy feeling successful for two seconds.
::endchoice

The clasp finally caught. Xu Ning put the damp, folded note back in her pocket.

::goto RETURN

::scene RETURN
## At the Door

::if knows_book
**A-He:** When you pick up the book on Friday, I'll come with you.

**Xu Ning:** You want to give the cactus your opinion?

**A-He:** I want to see the next balcony.
::elif repaired
**A-He:** This rib is straighter than it was.

**Xu Ning:** What a cautious compliment.
::else
Xu Ning turned the handle so A-He could take it easily.

**Xu Ning:** Don't leave it on the bus.

**A-He:** I'll talk to it the whole way so it remembers me.
::endif

::choice WALK
::option together | Wait while she locks up, then walk together to the corner.
A-He did not step down first. Xu Ning locked the door twice; the second time was only to check.

At the edge of the eaves, she shifted one shoulder a little closer to A-He.
::ending TOGETHER
::option ahead | Walk ahead, then turn back and wave.
A-He tried turning once in the rain. The umbrella did not dump water again.

When he looked back, Xu Ning was still under the eaves. She waved with her empty hand; this time it was not holding on to anything about to come apart.
::ending AHEAD
::endchoice
