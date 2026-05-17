'use client';

import { motion } from 'framer-motion';
import { ArrowRight, ShieldCheck, Star, Clock, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

const SERVICES = [
  { name: 'Plumbing', icon: '💧', desc: 'Fix leaks, install fixtures' },
  { name: 'Electrical', icon: '⚡', desc: 'Wiring, switch repair' },
  { name: 'Cleaning', icon: '🧹', desc: 'Deep cleaning, sanitization' },
  { name: 'Carpentry', icon: '🔨', desc: 'Furniture assembly, repairs' },
  { name: 'Painting', icon: '🎨', desc: 'Interior & exterior' },
  { name: 'AC Repair', icon: '❄️', desc: 'Service & installation' },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } }
};

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen selection:bg-emerald-500/30">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-slate-950 text-white pt-32 pb-20 sm:pt-40 sm:pb-28">
        {/* Animated Background Blobs */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full overflow-hidden -z-10">
          <div className="absolute top-[-10%] left-[20%] w-[500px] h-[500px] bg-emerald-500/20 rounded-full blur-[120px] mix-blend-screen animate-pulse duration-1000" />
          <div className="absolute top-[20%] right-[10%] w-[400px] h-[400px] bg-teal-500/20 rounded-full blur-[100px] mix-blend-screen" />
        </div>

        <motion.div 
          className="container relative mx-auto px-4 sm:px-6 lg:px-8 text-center z-10"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div variants={itemVariants} className="mb-6 flex justify-center">
            <span className="inline-flex items-center rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-sm font-medium text-emerald-300 backdrop-blur-sm">
              <Sparkles className="mr-2 h-4 w-4" /> Homeezy 2.0 is live
            </span>
          </motion.div>
          
          <motion.h1 
            variants={itemVariants}
            className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-slate-400"
          >
            Your Home Needs, <br className="hidden md:block" />
            <span className="text-emerald-400">Solved Instantly.</span>
          </motion.h1>
          
          <motion.p 
            variants={itemVariants}
            className="mt-4 text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            Book trusted, verified professionals for plumbing, electrical, cleaning, and more. Backed by our 100% satisfaction guarantee.
          </motion.p>
          
          <motion.div 
            variants={itemVariants}
            className="flex flex-col sm:flex-row justify-center items-center gap-4"
          >
            <Button size="lg" className="h-14 px-8 text-lg font-medium bg-emerald-500 hover:bg-emerald-600 text-white rounded-full w-full sm:w-auto shadow-[0_0_40px_-10px_rgba(16,185,129,0.5)] transition-all hover:shadow-[0_0_60px_-15px_rgba(16,185,129,0.7)] hover:-translate-y-0.5" asChild>
              <Link href="/services">
                Book a Service
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" className="h-14 px-8 text-lg font-medium bg-white/5 border-white/10 text-white hover:bg-white/10 hover:text-white rounded-full w-full sm:w-auto backdrop-blur-sm transition-all" asChild>
              <Link href="/register/worker">
                Become a Partner
              </Link>
            </Button>
          </motion.div>
        </motion.div>
      </section>

      {/* Categories Section */}
      <section className="py-24 bg-slate-50 relative">
        <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent" />
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4 tracking-tight">What do you need help with?</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">From quick fixes to major renovations, our experts are ready to assist you.</p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            {SERVICES.map((service, idx) => (
              <motion.div
                key={service.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: idx * 0.1, ease: "easeOut" }}
                viewport={{ once: true, margin: "-50px" }}
              >
                <Link href={`/services?category=${service.name.toLowerCase()}`}>
                  <Card className="h-full border-slate-200 shadow-sm hover:shadow-xl hover:border-emerald-200 transition-all duration-300 cursor-pointer group bg-white rounded-2xl overflow-hidden hover:-translate-y-1">
                    <CardContent className="p-6 flex flex-col items-center text-center h-full justify-center">
                      <div className="h-16 w-16 rounded-full bg-slate-50 flex items-center justify-center mb-4 group-hover:bg-emerald-50 transition-colors duration-300">
                        <span className="text-3xl group-hover:scale-110 transition-transform duration-300">{service.icon}</span>
                      </div>
                      <h3 className="font-semibold text-slate-900 mb-1">{service.name}</h3>
                      <p className="text-sm text-slate-500 line-clamp-2">{service.desc}</p>
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Why Choose Us */}
      <section className="py-24 bg-white relative">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 lg:gap-8">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="flex flex-col items-center text-center group"
            >
              <div className="h-20 w-20 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 group-hover:bg-emerald-100 group-hover:shadow-sm">
                <ShieldCheck className="h-10 w-10" />
              </div>
              <h3 className="text-xl font-bold mb-3 text-slate-900">Verified Professionals</h3>
              <p className="text-slate-600 leading-relaxed">Every worker undergoes strict background checks and comprehensive skill verification.</p>
            </motion.div>
            
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="flex flex-col items-center text-center group"
            >
              <div className="h-20 w-20 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 group-hover:bg-emerald-100 group-hover:shadow-sm">
                <Clock className="h-10 w-10" />
              </div>
              <h3 className="text-xl font-bold mb-3 text-slate-900">Instant Booking</h3>
              <p className="text-slate-600 leading-relaxed">Book in seconds. Our AI instantly matches you with the best available professional nearby.</p>
            </motion.div>
            
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="flex flex-col items-center text-center group"
            >
              <div className="h-20 w-20 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 group-hover:bg-emerald-100 group-hover:shadow-sm">
                <Star className="h-10 w-10" />
              </div>
              <h3 className="text-xl font-bold mb-3 text-slate-900">Quality Guaranteed</h3>
              <p className="text-slate-600 leading-relaxed">Your satisfaction is guaranteed. Unhappy with the service? We'll make it right.</p>
            </motion.div>
          </div>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="bg-slate-950 text-slate-400 py-12 border-t border-slate-900">
        <div className="container mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-white tracking-tight">Homeezy</span>
          </div>
          <p className="text-sm">© 2026 Homeezy. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
