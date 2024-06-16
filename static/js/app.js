gsap.registerPlugin(ScrollTrigger, ScrollSmoother)

ScrollSmoother.create({
   wrapper: '.wrapper',
   content: '.content',
   smooth: 2,
   effects: true 
})