import React from 'react';
import { Download, Tags, Search } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export function About() {
  const { t } = useTranslation();
  
  // 正确获取并处理类型
  const licenseTerms = t('about.license.terms', { returnObjects: true }) as string[];

  return (
    <main className="flex-grow max-w-4xl mx-auto px-6 sm:px-6 lg:px-8 py-6 sm:py-16">
      <div className="space-y-8 sm:space-y-16">
        {/* Header */}
        <div className="border-b border-gray-100 pb-4 sm:pb-0 sm:border-0">
          <h1 className="text-2xl sm:text-3xl font-medium text-gray-900 text-center sm:text-left">{t('about.title')}</h1>
        </div>

        {/* Mission */}
        <section className="px-1 sm:p-0 sm:shadow-none sm:rounded-none sm:bg-transparent">
          <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-3 sm:mb-4 text-center sm:text-left">
            {t('about.mission.title')}
          </h2>
          <p className="text-sm sm:text-lg text-gray-600 leading-relaxed">
            {t('about.mission.content')}
          </p>
        </section>

        {/* How to Use */}
        <section className="px-1 sm:p-0 sm:shadow-none sm:rounded-none sm:bg-transparent">
          <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 sm:mb-8 text-center sm:text-left">
            {t('about.howToUse.title')}
          </h2>
          <div className="space-y-5 sm:space-y-8">
            <div className="flex items-start gap-3 sm:gap-5 sm:bg-transparent sm:p-0 sm:rounded-none">
              <Search className="h-5 w-5 sm:h-6 sm:w-6 text-blue-600 stroke-[1.75] mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="text-sm sm:text-lg font-medium text-gray-900 mb-2 sm:mb-2">
                  {t('about.howToUse.search.title')}
                </h3>
                <p className="text-sm sm:text-lg text-gray-600 leading-relaxed">
                  {t('about.howToUse.search.content')}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 sm:gap-5 sm:bg-transparent sm:p-0 sm:rounded-none">
              <Tags className="h-5 w-5 sm:h-6 sm:w-6 text-blue-600 stroke-[1.75] mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="text-sm sm:text-lg font-medium text-gray-900 mb-2 sm:mb-2">
                  {t('about.howToUse.filter.title')}
                </h3>
                <p className="text-sm sm:text-lg text-gray-600 leading-relaxed">
                  {t('about.howToUse.filter.content')}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 sm:gap-5 sm:bg-transparent sm:p-0 sm:rounded-none">
              <Download className="h-5 w-5 sm:h-6 sm:w-6 text-blue-600 stroke-[1.75] mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="text-sm sm:text-lg font-medium text-gray-900 mb-2 sm:mb-2">
                  {t('about.howToUse.download.title')}
                </h3>
                <p className="text-sm sm:text-lg text-gray-600 leading-relaxed">
                  {t('about.howToUse.download.content')}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* License */}
        <section className="px-1 sm:p-0 sm:shadow-none sm:rounded-none sm:bg-transparent">
          <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-3 sm:mb-4 text-center sm:text-left">
            {t('about.license.title')}
          </h2>
          <p className="text-sm sm:text-lg text-gray-600 leading-relaxed mb-3 sm:mb-6">
            {t('about.license.intro')}
          </p>
          <ul className="text-sm sm:text-lg text-gray-600 space-y-2.5 sm:space-y-3 pl-2">
            {licenseTerms.map((term, index) => (
              <li key={index} className="flex items-start gap-2 sm:gap-3">
                <span className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-1.5"></span>
                <span>{term}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* Contact */}
        <section className="px-1 sm:p-0 sm:shadow-none sm:rounded-none sm:bg-transparent">
          <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-3 sm:mb-4 text-center sm:text-left">
            {t('about.contact.title')}
          </h2>
          <p className="text-sm sm:text-lg text-gray-600 leading-relaxed mb-3 sm:mb-6">
            {t('about.contact.intro')}
          </p>
          <div className="space-y-1 sm:space-y-2 text-sm sm:text-lg text-gray-600 sm:bg-transparent sm:p-0 sm:rounded-none">
            <p>{t('about.contact.email')}</p>
          </div>
        </section>
      </div>
    </main>
  );
}

export default About;