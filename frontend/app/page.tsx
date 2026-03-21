import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="max-w-4xl mx-auto py-24 animate-fade" data-route="landing">
      <section className="mb-32">
        <h1 className="text-7xl md:text-9xl font-bold tracking-tighter mb-12 uppercase leading-[0.8]">
          Zia <br /> News
        </h1>
        <p className="text-xl max-w-lg mb-12 opacity-60 leading-relaxed">
          Information without noise. A strictly minimalist AI news engine powered by intelligence.
        </p>
        <Link
          href="/feed"
          className="btn-minimal-inverse text-lg font-bold uppercase tracking-widest"
        >
          Enter Dashboard
        </Link>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-24 mb-32">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-[0.3em] mb-6 opacity-40">Concept</h2>
          <p className="text-lg leading-relaxed">
            We believe in the power of subtraction. By removing color, complex layouts, and unnecessary features, we focus on what matters: the content.
          </p>
        </div>
        <div>
          <h2 className="text-xs font-bold uppercase tracking-[0.3em] mb-6 opacity-40">Technology</h2>
          <p className="text-lg leading-relaxed">
            Advanced language models analyze thousands of sources to provide you with the most relevant, verified information in seconds.
          </p>
        </div>
      </section>

      <section className="border-t border-black dark:border-white py-24">
        <div className="flex flex-col md:flex-row justify-between items-start gap-12">
          <div className="text-6xl font-bold tracking-tighter">01</div>
          <div className="max-w-xs">
            <h3 className="font-bold uppercase mb-4">Intelligence</h3>
            <p className="text-sm opacity-60">Automated summaries that capture the essence of every story.</p>
          </div>
          <div className="text-6xl font-bold tracking-tighter">02</div>
          <div className="max-w-xs">
            <h3 className="font-bold uppercase mb-4">Trust</h3>
            <p className="text-sm opacity-60">Proprietary scoring system to ensure source reliability.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
